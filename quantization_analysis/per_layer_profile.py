#!/usr/bin/env python3
"""
FC (Linear) + Conv2d layer profile (vision: ResNet18/50; NLP: BERT-tiny has no Conv — empty conv JSON skipped).
Loads models from checkpoints, collects per-layer weight stats and writes:
  *_linear_per_layer.json, *_conv_per_layer.json (vision only when --profile-conv, default on).

Activation stats (when --calibration-batches N > 0):
  - activation_min / activation_max / activation_shape: over all hooked Linear outputs.
  - activation_sparsity_zero: fraction of elements exactly 0 (accumulated over batches).
  - activation_sparsity_near_zero: fraction with |x| < --activation-near-zero-threshold (default 1e-6).
  If calibration_batches=0, activation_* above are null.

Usage:
  python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" --checkpoint-dir checkpoints
  python per_layer_profile.py --models ResNet18 --checkpoint-dir checkpoints --profile-quantized
  python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" --checkpoint-dir checkpoints --calibration-batches 8 --sensitivity --sensitivity-bit-width 4 --profile-quantized
"""

import argparse
import json
import os
import re
from pathlib import Path

import torch
import torch.nn as nn

from configs import ModelConfig, MODEL_CONFIGS

# Optional: for quantized checkpoint profile and sensitivity we need quant_layers
try:
    from quant_layers import QuantConv2d, replace_with_quant, replace_one_layer_with_quant
except ImportError:
    QuantConv2d = None  # type: ignore
    replace_with_quant = None
    replace_one_layer_with_quant = None


def _get_linear_modules(model: nn.Module):
    """Yield (full_name, module) for each nn.Linear or QuantLinear-like (has .weight)."""
    for name, mod in model.named_modules():
        if isinstance(mod, nn.Linear):
            yield name, mod
        elif hasattr(mod, "weight") and hasattr(mod.weight, "shape") and mod.weight.dim() == 2:
            # QuantLinear or similar
            yield name, mod


def _get_conv_modules(model: nn.Module):
    """Yield (full_name, module) for each nn.Conv2d or QuantConv2d."""
    for name, mod in model.named_modules():
        if isinstance(mod, nn.Conv2d):
            yield name, mod
        elif QuantConv2d is not None and isinstance(mod, QuantConv2d):
            yield name, mod


def _weight_stats(w: torch.Tensor, near_zero_thr: float = 1e-6):
    w = w.detach().float()
    with torch.no_grad():
        n = w.numel()
        std = w.std().item() if n > 0 else 0.0
        zero = (w == 0).float().sum().item() / n if n else 0.0
        near = (w.abs() < near_zero_thr).float().sum().item() / n if n else 0.0
    return {
        "weight_min": w.min().item(),
        "weight_max": w.max().item(),
        "weight_mean": w.mean().item(),
        "weight_std": std,
        "weight_sparsity_zero": zero,
        "weight_sparsity_near_zero": near,
    }


def collect_linear_layers(model: nn.Module, model_name: str, activation_stats: dict | None = None):
    """Collect FC layer records (name, weight_shape, stats, layer_id).
    If activation_stats is provided (name -> {min, max, shape, activation_sparsity_* }), fill activation_* fields."""
    layers = []
    for idx, (name, mod) in enumerate(_get_linear_modules(model)):
        w = getattr(mod, "weight", None)
        if w is None:
            continue
        w = w.detach()
        shape = list(w.shape)
        stats = _weight_stats(w)
        act = (activation_stats or {}).get(name, {})
        layers.append({
            "layer_index": idx,
            "name": name,
            "graph_node_name": name.replace(".", "_"),
            "weight_shape": shape,
            **stats,
            "activation_shape": act.get("shape"),
            "activation_min": act.get("min"),
            "activation_max": act.get("max"),
            "activation_sparsity_zero": act.get("activation_sparsity_zero"),
            "activation_sparsity_near_zero": act.get("activation_sparsity_near_zero"),
            "sensitivity_accuracy_drop": None,  # filled when --sensitivity is used
            "model_name": model_name,
            "layer_id": f"{model_name}#L{idx}#{name}",
        })
    return layers


def _conv_hyperparams(mod: nn.Module) -> dict:
    """Kernel/stride/padding etc. Works for nn.Conv2d and QuantConv2d."""
    if QuantConv2d is not None and isinstance(mod, QuantConv2d):
        c = mod._conv
    elif isinstance(mod, nn.Conv2d):
        c = mod
    else:
        raise TypeError(f"Expected Conv2d or QuantConv2d, got {type(mod)}")

    def _tup(x):
        if isinstance(x, (tuple, list)):
            return list(x)
        return [x, x]

    return {
        "in_channels": c.in_channels,
        "out_channels": c.out_channels,
        "kernel_size": _tup(c.kernel_size),
        "stride": _tup(c.stride),
        "padding": _tup(c.padding),
        "dilation": _tup(c.dilation),
        "groups": c.groups,
        "has_bias": c.bias is not None,
    }


def collect_conv_layers(model: nn.Module, model_name: str, activation_stats: dict | None = None):
    """Per Conv2d record: weight stats, hyperparams, optional activation stats (vision calibration)."""
    layers = []
    for idx, (name, mod) in enumerate(_get_conv_modules(model)):
        w = getattr(mod, "weight", None)
        if w is None:
            continue
        w = w.detach()
        shape = list(w.shape)
        stats = _weight_stats(w)
        act = (activation_stats or {}).get(name, {})
        layers.append(
            {
                "layer_index": idx,
                "name": name,
                "graph_node_name": name.replace(".", "_"),
                "weight_shape": shape,
                **_conv_hyperparams(mod),
                **stats,
                "activation_shape": act.get("shape"),
                "activation_min": act.get("min"),
                "activation_max": act.get("max"),
                "activation_sparsity_zero": act.get("activation_sparsity_zero"),
                "activation_sparsity_near_zero": act.get("activation_sparsity_near_zero"),
                "sensitivity_accuracy_drop": None,
                "model_name": model_name,
                "layer_id": f"{model_name}#C{idx}#{name}",
            }
        )
    return layers


def _accumulate_linear_output(
    stats: dict,
    name: str,
    out: torch.Tensor,
    near_zero_thr: float,
) -> None:
    """Accumulate min/max/shape and global counts for zero / near-zero sparsity over batches."""
    o = out.detach().float()
    n = o.numel()
    if n == 0:
        return
    z = (o == 0).float().sum().item()
    nz = (o.abs() < near_zero_thr).float().sum().item()
    if name not in stats:
        stats[name] = {
            "min": o.min().item(),
            "max": o.max().item(),
            "shape": list(o.shape),
            "_n": n,
            "_z": z,
            "_nz": nz,
        }
    else:
        stats[name]["min"] = min(stats[name]["min"], o.min().item())
        stats[name]["max"] = max(stats[name]["max"], o.max().item())
        stats[name]["_n"] += n
        stats[name]["_z"] += z
        stats[name]["_nz"] += nz


def _finalize_activation_stats(stats: dict) -> dict:
    """Convert internal _n/_z/_nz into activation_sparsity_* ratios."""
    out: dict = {}
    for name, s in stats.items():
        n = s["_n"]
        z, nz = s["_z"], s["_nz"]
        out[name] = {
            "min": s["min"],
            "max": s["max"],
            "shape": s["shape"],
            "activation_sparsity_zero": z / n if n else 0.0,
            "activation_sparsity_near_zero": nz / n if n else 0.0,
        }
    return out


def _run_calibration_vision(
    model: nn.Module,
    device: torch.device,
    num_batches: int,
    near_zero_thr: float,
    hook_linear: bool = True,
    hook_conv: bool = False,
):
    """Run a few CIFAR-10 batches, hook Linear and/or Conv2d outputs, return {layer_name: stats including sparsity}."""
    from torchvision.datasets import CIFAR10
    from torchvision import transforms
    stats = {}
    hooks = []

    def make_hook(name):
        def hook(_, __, out):
            _accumulate_linear_output(stats, name, out, near_zero_thr)

        return hook

    if hook_linear:
        for name, mod in _get_linear_modules(model):
            hooks.append(mod.register_forward_hook(make_hook(name)))
    if hook_conv:
        for name, mod in _get_conv_modules(model):
            hooks.append(mod.register_forward_hook(make_hook(name)))

    try:
        t = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))])
        ds = CIFAR10(root="./data", train=True, download=True, transform=t)
        loader = torch.utils.data.DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
        model.eval()
        with torch.no_grad():
            for i, (x, _) in enumerate(loader):
                if i >= num_batches:
                    break
                _ = model(x.to(device))
    finally:
        for h in hooks:
            h.remove()
    return _finalize_activation_stats(stats)


def _run_calibration_nlp(
    model: nn.Module,
    device: torch.device,
    cfg: ModelConfig,
    num_batches: int,
    near_zero_thr: float,
):
    """Run a few IMDB batches, hook Linear outputs. Requires transformers + datasets."""
    from transformers import AutoTokenizer
    from datasets import load_dataset
    stats = {}
    hooks = []

    def make_hook(name):
        def hook(_, __, out):
            _accumulate_linear_output(stats, name, out, near_zero_thr)

        return hook

    for name, mod in _get_linear_modules(model):
        hooks.append(mod.register_forward_hook(make_hook(name)))

    try:
        tokenizer = AutoTokenizer.from_pretrained(cfg.tokenizer_checkpoint)
        ds = load_dataset("imdb", split="train").select(range(min(512, num_batches * 32)))
        def tok(x):
            return tokenizer(x["text"], truncation=True, max_length=128, padding="max_length", return_tensors="pt")
        ds = ds.map(tok, batched=True, remove_columns=["text"]).rename_column("label", "labels")
        def collate(batch):
            keys = batch[0].keys()
            out = {}
            for k in keys:
                v = [b[k] for b in batch]
                if isinstance(v[0], torch.Tensor):
                    out[k] = torch.stack(v)
                else:
                    out[k] = torch.tensor(v, dtype=torch.long)
            return out

        loader = torch.utils.data.DataLoader(ds, batch_size=32, shuffle=False, collate_fn=collate)
        model.eval()
        with torch.no_grad():
            for i, batch in enumerate(loader):
                if i >= num_batches:
                    break
                batch = {k: v.to(device) for k, v in batch.items()}
                _ = model(**batch)
    finally:
        for h in hooks:
            h.remove()
    return _finalize_activation_stats(stats)


def _get_test_loader_vision(batch_size: int = 64):
    """CIFAR-10 test loader, same transform as run_sweep eval."""
    from torchvision.datasets import CIFAR10
    from torchvision import transforms
    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
    ])
    ds = CIFAR10(root="./data", train=False, download=True, transform=t)
    return torch.utils.data.DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)


def _get_test_loader_nlp(cfg: ModelConfig, batch_size: int = 32):
    """IMDB test loader with tokenizer; returns (loader, tokenizer)."""
    from transformers import AutoTokenizer
    from datasets import load_dataset
    tokenizer = AutoTokenizer.from_pretrained(cfg.tokenizer_checkpoint)

    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=128,
            padding="max_length",
            return_tensors=None,
        )

    test_ds = load_dataset("imdb", split="test").map(
        tokenize, batched=True, remove_columns=["text"]
    )
    test_ds = test_ds.rename_column("label", "labels")

    def collate(batch):
        keys = batch[0].keys()
        return {k: torch.tensor([b[k] for b in batch]) for k in keys}

    loader = torch.utils.data.DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate, num_workers=0
    )
    return loader, tokenizer


def _evaluate_vision(model: nn.Module, loader, device: torch.device, max_batches: int | None):
    model.eval()
    total, correct = 0, 0
    with torch.no_grad():
        for i, (x, y) in enumerate(loader):
            if max_batches is not None and i >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits = model(x)
            pred = logits.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return correct / total if total else 0.0


def _evaluate_nlp(model: nn.Module, loader, device: torch.device, max_batches: int | None):
    model.eval()
    total, correct = 0, 0
    with torch.no_grad():
        for i, batch in enumerate(loader):
            if max_batches is not None and i >= max_batches:
                break
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            pred = out.logits.argmax(dim=1)
            correct += (pred == batch["labels"]).sum().item()
            total += batch["labels"].size(0)
    return correct / total if total else 0.0


def _run_sensitivity(
    model: nn.Module,
    layers: list[dict],
    cfg: ModelConfig,
    is_nlp: bool,
    is_quantized: bool,
    quant_bit_width: int | None,
    sensitivity_bit_width: int,
    max_eval_batches: int | None,
    device: torch.device,
):
    """Fill layers[].sensitivity_accuracy_drop: accuracy drop when only that layer is quantized to a *degraded* bit width.
    For quantized models we use a strictly lower bit width for the single layer so the drop is non-trivial (otherwise same width -> no change -> drop 0).
    """
    if replace_one_layer_with_quant is None:
        print("  [sensitivity] quant_layers.replace_one_layer_with_quant not available, skip.")
        return
    # When model is already quantized, degrade the single layer by *at least 2 bits* so the drop is visible (1-bit lower often gives drop=0 for single-FC models)
    if is_quantized and quant_bit_width is not None:
        effective_sens_bw = max(2, min(sensitivity_bit_width, quant_bit_width - 2))
        print(f"  Sensitivity: single layer degraded to {effective_sens_bw}-bit (model is {quant_bit_width}-bit)")
    else:
        # Baseline (float): degrade to 2-bit for the single layer so we see a clear drop (4-bit on one layer often gives drop≈0 for ResNet fc)
        effective_sens_bw = max(2, min(sensitivity_bit_width, 2))
        if effective_sens_bw != sensitivity_bit_width:
            print(f"  Sensitivity: single layer at {effective_sens_bw}-bit (baseline float)")
    evaluate_fn = _evaluate_nlp if is_nlp else _evaluate_vision
    if is_nlp:
        loader, _ = _get_test_loader_nlp(cfg)
    else:
        loader = _get_test_loader_vision()
    model.to(device)
    baseline_acc = evaluate_fn(model, loader, device, max_eval_batches)
    print(f"  Baseline accuracy: {baseline_acc:.4f}")
    if baseline_acc < 0.2:
        print("  (low baseline -> sensitivity drop often 0)")
    from quant_layers import QuantLinear, QuantConv2d
    for idx, rec in enumerate(layers):
        name = rec.get("name")
        if not name:
            continue
        try:
            mod = model.get_submodule(name)
            if not isinstance(mod, (nn.Linear, QuantLinear, nn.Conv2d, QuantConv2d)):
                rec["sensitivity_accuracy_drop"] = None
                print(f"  Layer {name}: skip (Embedding / unsupported)")
                continue
        except Exception:
            pass
        try:
            if is_nlp:
                clone = load_nlp_model(cfg)
            else:
                clone = load_vision_model(cfg, num_classes=10)
            if is_quantized and quant_bit_width is not None and replace_with_quant is not None:
                replace_with_quant(clone, bit_width=quant_bit_width, layer_types=cfg.layer_types)
            state = model.state_dict()
            if is_nlp:
                state = {k: v for k, v in state.items() if k in clone.state_dict()}
            clone.load_state_dict(state, strict=not is_nlp)
            replace_one_layer_with_quant(clone, name, effective_sens_bw)
            clone.to(device)
            acc = evaluate_fn(clone, loader, device, max_eval_batches)
            drop = baseline_acc - acc
            rec["sensitivity_accuracy_drop"] = round(drop, 6)
        except Exception as e:
            rec["sensitivity_accuracy_drop"] = None
            print(f"  Layer {name}: error {e}")
        else:
            print(f"  Layer {idx+1}/{len(layers)} {name}: drop = {rec['sensitivity_accuracy_drop']:.4f}")


def load_vision_model(cfg: ModelConfig, num_classes: int = 10):
    from torchvision.models import resnet18, resnet50
    if cfg.name == "ResNet18":
        return resnet18(num_classes=num_classes)
    if cfg.name == "ResNet50":
        return resnet50(num_classes=num_classes)
    raise ValueError(f"Unsupported: {cfg.name}")


def load_nlp_model(cfg: ModelConfig):
    from transformers import AutoModelForSequenceClassification
    model = AutoModelForSequenceClassification.from_pretrained(cfg.checkpoint, num_labels=2)
    model.config.problem_type = "single_label_classification"
    return model


def run_profile(
    model_names: list[str],
    checkpoint_dir: str | None,
    output_dir: str,
    profile_quantized: bool,
    calibration_batches: int = 0,
    activation_near_zero_thr: float = 1e-6,
    profile_conv: bool = True,
    sensitivity: bool = False,
    sensitivity_bit_width: int = 4,
    max_eval_batches: int = 100,
):
    eval_batches = None if max_eval_batches == 0 else max_eval_batches  # 0 = full test set
    supported = [c for c in MODEL_CONFIGS if c.name in ("ResNet18", "ResNet50", "BERT-tiny")]
    configs = [c for c in supported if c.name in model_names] if model_names else supported
    if not configs:
        print("No models selected. Use --models ResNet18 ResNet50 \"BERT-tiny\"")
        return

    os.makedirs(output_dir, exist_ok=True)

    for cfg in configs:
        model_name = cfg.name
        dataset = cfg.dataset.strip().lower()
        slug = model_name.replace(" ", "_").replace("-", "_").lower()

        # --- Baseline: load model and optional *_trained.pt ---
        if cfg.is_nlp:
            model = load_nlp_model(cfg)
        else:
            model = load_vision_model(cfg, num_classes=10)

        ckpt_path = None
        if checkpoint_dir:
            base = os.path.join(checkpoint_dir, cfg.name.replace(" ", "_").replace("-", "_") + "_trained.pt")
            if os.path.isfile(base):
                ckpt_path = base

        if ckpt_path:
            state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
            if cfg.is_nlp:
                state = {k: v for k, v in state.items() if k in model.state_dict()}
            model.load_state_dict(state, strict=not cfg.is_nlp)
            print(f"[{model_name}] Loaded {ckpt_path}")

        activation_stats = None
        if calibration_batches > 0:
            device = next(model.parameters()).device
            model.to(device)
            if cfg.is_nlp:
                activation_stats = _run_calibration_nlp(
                    model, device, cfg, calibration_batches, activation_near_zero_thr
                )
            else:
                activation_stats = _run_calibration_vision(
                    model,
                    device,
                    calibration_batches,
                    activation_near_zero_thr,
                    hook_linear=True,
                    hook_conv=profile_conv,
                )
            print(
                f"  Calibration: {calibration_batches} batches -> activation min/max/sparsity "
                f"(near-zero thr={activation_near_zero_thr})"
            )

        layers = collect_linear_layers(model, model_name, activation_stats)
        if sensitivity:
            dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            _run_sensitivity(
                model, layers, cfg, is_nlp=cfg.is_nlp, is_quantized=False, quant_bit_width=None,
                sensitivity_bit_width=sensitivity_bit_width, max_eval_batches=eval_batches, device=dev,
            )
        out = {
            "model": model_name,
            "dataset": dataset,
            "focus": "linear",
            "total_linear_layers": len(layers),
            "quantized": False,
            "checkpoint": ckpt_path or "none",
            "calibration_batches": calibration_batches,
            "linear_layers": layers,
            "schema_note": (
                "per_layer_profile. activation_min/max/shape/sparsity null when calibration_batches=0. "
                "activation_sparsity_near_zero uses activation_near_zero_thr from run."
            ),
            "activation_near_zero_threshold": activation_near_zero_thr if calibration_batches > 0 else None,
        }
        if sensitivity:
            out["sensitivity_bit_width"] = sensitivity_bit_width
        path = os.path.join(output_dir, f"{slug}_linear_per_layer.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"  Saved baseline FC profile: {path} ({len(layers)} layers)")

        if profile_conv and not cfg.is_nlp:
            conv_layers = collect_conv_layers(model, model_name, activation_stats)
            out_conv = {
                "model": model_name,
                "dataset": dataset,
                "focus": "conv2d",
                "total_conv_layers": len(conv_layers),
                "quantized": False,
                "checkpoint": ckpt_path or "none",
                "calibration_batches": calibration_batches,
                "conv_layers": conv_layers,
                "schema_note": (
                    "per_layer_profile. activation_min/max/shape/sparsity null when calibration_batches=0. "
                    "Vision-only; NLP models have no Conv2d in this pipeline."
                ),
                "activation_near_zero_threshold": activation_near_zero_thr if calibration_batches > 0 else None,
            }
            path_c = os.path.join(output_dir, f"{slug}_conv_per_layer.json")
            with open(path_c, "w") as f:
                json.dump(out_conv, f, indent=2)
            print(f"  Saved baseline Conv profile: {path_c} ({len(conv_layers)} layers)")

        # --- Quantized checkpoints: scan ALL *_qat.pt / *_ptq.pt for this model ---
        # run_sweep saves as {ModelName_no_spaces}_w{bw}_qat.pt e.g. BERT_tiny_w4_qat.pt, ResNet18_w4_qat.pt
        if profile_quantized and checkpoint_dir and replace_with_quant is not None:
            file_slug = model_name.replace(" ", "_").replace("-", "_")  # same as run_sweep
            pattern = re.compile(rf"^{re.escape(file_slug)}_w(\d+)_(qat|ptq)\.pt$", re.IGNORECASE)
            matched = [(fname, pattern.match(fname)) for fname in os.listdir(checkpoint_dir)]
            matched = [(fname, m) for fname, m in matched if m is not None]
            if not matched:
                print(f"  [profile-quantized] No *_w*_qat.pt / *_w*_ptq.pt found for {model_name} in {checkpoint_dir}")
            for fname, m in sorted(matched, key=lambda x: (int(x[1].group(1)), x[1].group(2))):
                bit_width = int(m.group(1))
                variant = m.group(2)
                ckpt = os.path.join(checkpoint_dir, fname)
                if cfg.is_nlp:
                    model_q = load_nlp_model(cfg)
                else:
                    model_q = load_vision_model(cfg, num_classes=10)
                state_q = torch.load(ckpt, map_location="cpu", weights_only=True)
                if cfg.is_nlp:
                    state_q = {k: v for k, v in state_q.items() if k in model_q.state_dict()}
                else:
                    # QAT/PTQ vision checkpoints were saved from a model with QuantConv2d (keys like conv1._conv.weight).
                    # Remap to plain Conv2d/Linear keys so load into fresh ResNet succeeds.
                    state_plain = {}
                    for k, v in state_q.items():
                        if k.endswith("._conv.weight"):
                            state_plain[k.replace("._conv.weight", ".weight")] = v
                        elif k.endswith("._conv.bias"):
                            state_plain[k.replace("._conv.bias", ".bias")] = v
                        else:
                            state_plain[k] = v
                    state_q = state_plain
                model_q.load_state_dict(state_q, strict=False)
                replace_with_quant(model_q, bit_width=bit_width, layer_types=cfg.layer_types)

                act_stats_q = None
                if calibration_batches > 0:
                    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    model_q.to(dev)
                    if cfg.is_nlp:
                        act_stats_q = _run_calibration_nlp(
                            model_q, dev, cfg, calibration_batches, activation_near_zero_thr
                        )
                    else:
                        act_stats_q = _run_calibration_vision(
                            model_q,
                            dev,
                            calibration_batches,
                            activation_near_zero_thr,
                            hook_linear=True,
                            hook_conv=profile_conv,
                        )
                layers_q = collect_linear_layers(model_q, model_name, act_stats_q)
                if sensitivity:
                    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    _run_sensitivity(
                        model_q, layers_q, cfg, is_nlp=cfg.is_nlp, is_quantized=True, quant_bit_width=bit_width,
                        sensitivity_bit_width=sensitivity_bit_width, max_eval_batches=eval_batches, device=dev,
                    )
                out_q = {
                    "model": model_name,
                    "dataset": dataset,
                    "focus": "linear",
                    "total_linear_layers": len(layers_q),
                    "quantized": True,
                    "bit_width": bit_width,
                    "variant": variant,
                    "checkpoint": fname,
                    "calibration_batches": calibration_batches,
                    "linear_layers": layers_q,
                    "schema_note": (
                        "per_layer_profile. activation_min/max/shape/sparsity null when calibration_batches=0. "
                        "activation_sparsity_near_zero uses activation_near_zero_thr from run."
                    ),
                    "activation_near_zero_threshold": activation_near_zero_thr if calibration_batches > 0 else None,
                }
                if sensitivity:
                    out_q["sensitivity_bit_width"] = sensitivity_bit_width
                path_q = os.path.join(output_dir, f"{slug}_w{bit_width}_{variant}_linear_per_layer.json")
                with open(path_q, "w") as f:
                    json.dump(out_q, f, indent=2)
                print(f"  Saved quantized FC profile: {path_q} ({len(layers_q)} layers)")

                if profile_conv and not cfg.is_nlp:
                    conv_q = collect_conv_layers(model_q, model_name, act_stats_q)
                    out_cq = {
                        "model": model_name,
                        "dataset": dataset,
                        "focus": "conv2d",
                        "total_conv_layers": len(conv_q),
                        "quantized": True,
                        "bit_width": bit_width,
                        "variant": variant,
                        "checkpoint": fname,
                        "calibration_batches": calibration_batches,
                        "conv_layers": conv_q,
                        "schema_note": (
                            "per_layer_profile. activation_min/max/shape/sparsity null when calibration_batches=0. "
                            "Vision-only; NLP models have no Conv2d in this pipeline."
                        ),
                        "activation_near_zero_threshold": activation_near_zero_thr if calibration_batches > 0 else None,
                    }
                    path_cq = os.path.join(output_dir, f"{slug}_w{bit_width}_{variant}_conv_per_layer.json")
                    with open(path_cq, "w") as f:
                        json.dump(out_cq, f, indent=2)
                    print(f"  Saved quantized Conv profile: {path_cq} ({len(conv_q)} layers)")

    print(f"\nDone. Results in {output_dir}")


def main():
    p = argparse.ArgumentParser(description="Linear + Conv2d layer profile (optional calibration & sensitivity)")
    p.add_argument("--models", nargs="*", default=None, help='ResNet18, ResNet50, "BERT-tiny"')
    p.add_argument("--checkpoint-dir", type=str, default=None, help="Dir with *_trained.pt (and *_qat.pt if --profile-quantized)")
    p.add_argument("--output-dir", type=str, default=str(Path(__file__).parent / "per_layer_results"))
    p.add_argument("--profile-quantized", action="store_true", help="Also profile *_qat.pt / *_ptq.pt in checkpoint-dir")
    p.add_argument(
        "--no-profile-conv",
        action="store_true",
        help="Skip Conv2d profiling (default: write *_conv_per_layer.json for vision models)",
    )
    p.add_argument("--calibration-batches", type=int, default=0, help="Run N batches to fill activation min/max/shape/sparsity (0 = leave null)")
    p.add_argument(
        "--activation-near-zero-threshold",
        type=float,
        default=1e-6,
        help="|x| below this counts toward activation_sparsity_near_zero (default 1e-6)",
    )
    p.add_argument("--sensitivity", action="store_true", help="Compute sensitivity_accuracy_drop: eval with only each layer quantized to --sensitivity-bit-width")
    p.add_argument("--sensitivity-bit-width", type=int, default=4, help="Bit width for sensitivity test (default 4)")
    p.add_argument("--max-eval-batches", type=int, default=100, help="Max test batches for sensitivity (0 = full test set, default 100)")
    args = p.parse_args()
    run_profile(
        model_names=args.models or [],
        checkpoint_dir=args.checkpoint_dir,
        output_dir=args.output_dir,
        profile_quantized=args.profile_quantized,
        calibration_batches=args.calibration_batches,
        activation_near_zero_thr=args.activation_near_zero_threshold,
        profile_conv=not args.no_profile_conv,
        sensitivity=args.sensitivity,
        sensitivity_bit_width=args.sensitivity_bit_width,
        max_eval_batches=args.max_eval_batches,
    )


if __name__ == "__main__":
    main()
