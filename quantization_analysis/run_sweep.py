#!/usr/bin/env python3
"""
Quantization sweep: pure PyTorch + torchvision + transformers.
Vision: ResNet18/50 on CIFAR-10. NLP: BERT-tiny on IMDB.
Uses local quant_layers.QuantLinear / QuantConv2d (integer quantization, STE for QAT).

Usage:
    python run_sweep.py --models ResNet18 ResNet50 --bit-widths 4 8 16 --train-epochs 10 --run-qat --qat-epochs 3 --save-checkpoint-dir checkpoints
    python run_sweep.py --models "BERT-tiny" --bit-widths 4 8 16 --train-epochs 3 --run-qat --qat-epochs 2 --save-checkpoint-dir checkpoints
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
import pytorch_lightning as pl
from torch.utils.data import DataLoader, random_split
from torchvision import transforms
from torchvision.datasets import CIFAR10
from torchvision.models import resnet18, resnet50

from configs import ModelConfig, MODEL_CONFIGS, BIT_WIDTHS

from quant_layers import replace_with_quant, QuantLinear, QuantConv2d


# ---------------------------------------------------------------------------
# Dataset: CIFAR-10
# ---------------------------------------------------------------------------

def get_cifar10_dataloaders(batch_size: int, num_workers: int = 0):
    """Train / val / test DataLoaders for CIFAR-10."""
    normalize = transforms.Normalize(
        (0.4914, 0.4822, 0.4465),
        (0.2023, 0.1994, 0.2010),
    )
    train_t = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        normalize,
    ])
    eval_t = transforms.Compose([transforms.ToTensor(), normalize])

    train_full = CIFAR10(root="./data", train=True, download=True, transform=train_t)
    train_val = CIFAR10(root="./data", train=True, download=True, transform=eval_t)
    test_ds = CIFAR10(root="./data", train=False, download=True, transform=eval_t)
    n_train = int(0.9 * len(train_full))
    n_val = len(train_full) - n_train
    train_ds, _ = random_split(train_full, [n_train, n_val])
    _, val_ds = random_split(train_val, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader, test_loader


# ---------------------------------------------------------------------------
# Dataset: IMDB for BERT
# ---------------------------------------------------------------------------

def get_imdb_dataloaders(cfg: ModelConfig, batch_size: int, max_length: int = 128, num_workers: int = 0):
    """Train / val / test DataLoaders for IMDB with tokenizer from cfg."""
    from transformers import AutoTokenizer
    from datasets import load_dataset

    tokenizer = AutoTokenizer.from_pretrained(cfg.tokenizer_checkpoint)

    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_length,
            padding="max_length",
            return_tensors=None,
        )

    ds = load_dataset("imdb")
    train_ds = ds["train"].map(tokenize, batched=True, remove_columns=["text"])
    train_ds = train_ds.rename_column("label", "labels")
    test_ds = ds["test"].map(tokenize, batched=True, remove_columns=["text"])
    test_ds = test_ds.rename_column("label", "labels")

    n_train = len(train_ds)
    n_val = max(1, n_train // 10)
    n_train = n_train - n_val
    train_ds, val_ds = random_split(train_ds, [n_train, n_val])

    def collate(batch):
        keys = batch[0].keys()
        return {k: torch.tensor([b[k] for b in batch]) for k in keys}

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, collate_fn=collate, num_workers=num_workers)
    return train_loader, val_loader, test_loader, tokenizer


# ---------------------------------------------------------------------------
# Model loading (torchvision / transformers, no chop)
# ---------------------------------------------------------------------------

def load_vision_model(cfg: ModelConfig, num_classes: int = 10):
    """Load ResNet18 or ResNet50 for CIFAR-10 (num_classes=10)."""
    if cfg.name == "ResNet18":
        model = resnet18(num_classes=num_classes)
    elif cfg.name == "ResNet50":
        model = resnet50(num_classes=num_classes)
    else:
        raise ValueError(f"Unsupported model: {cfg.name}. Use ResNet18 or ResNet50.")
    return model


def load_nlp_model(cfg: ModelConfig):
    """Load BERT-tiny (or other HF) for sequence classification."""
    from transformers import AutoModelForSequenceClassification
    model = AutoModelForSequenceClassification.from_pretrained(cfg.checkpoint, num_labels=2)
    model.config.problem_type = "single_label_classification"
    return model


# ---------------------------------------------------------------------------
# Lightning wrapper for train / test
# ---------------------------------------------------------------------------

class VisionWrapper(pl.LightningModule):
    def __init__(self, model: nn.Module, lr: float = 1e-3):
        super().__init__()
        self.model = model
        self.lr = lr

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self.model(x)
        loss = nn.functional.cross_entropy(logits, y)
        self.log("train_loss", loss, on_step=True, prog_bar=False)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self.model(x)
        loss = nn.functional.cross_entropy(logits, y)
        pred = logits.argmax(dim=1)
        acc = (pred == y).float().mean()
        self.log("val_loss_epoch", loss)
        self.log("val_acc_epoch", acc)
        return loss

    def test_step(self, batch, batch_idx):
        x, y = batch
        logits = self.model(x)
        loss = nn.functional.cross_entropy(logits, y)
        pred = logits.argmax(dim=1)
        acc = (pred == y).float().mean()
        self.log("test_loss_epoch", loss)
        self.log("test_acc_epoch", acc)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.model.parameters(), lr=self.lr)


class NLPWrapper(pl.LightningModule):
    """Wrapper for HuggingFace sequence classification (BERT-tiny on IMDB)."""

    def __init__(self, model: nn.Module, lr: float = 2e-5):
        super().__init__()
        self.model = model
        self.lr = lr

    def forward(self, **batch):
        return self.model(**batch)

    def training_step(self, batch, batch_idx):
        out = self.model(**batch)
        loss = out.loss
        self.log("train_loss", loss, on_step=True, prog_bar=False)
        return loss

    def validation_step(self, batch, batch_idx):
        out = self.model(**batch)
        self.log("val_loss_epoch", out.loss)
        pred = out.logits.argmax(dim=1)
        acc = (pred == batch["labels"]).float().mean()
        self.log("val_acc_epoch", acc)
        return out.loss

    def test_step(self, batch, batch_idx):
        out = self.model(**batch)
        self.log("test_loss_epoch", out.loss)
        pred = out.logits.argmax(dim=1)
        acc = (pred == batch["labels"]).float().mean()
        self.log("test_acc_epoch", acc)
        return out.loss

    def configure_optimizers(self):
        return torch.optim.AdamW(self.model.parameters(), lr=self.lr)


# ---------------------------------------------------------------------------
# PTQ verification: ensure we really quantized and different bw => different output
# ---------------------------------------------------------------------------

def _verify_ptq_vision(
    model_baseline: nn.Module,
    model_quant: nn.Module,
    test_loader: DataLoader,
    bit_width: int,
    device: torch.device,
    num_batches_check: int = 5,
) -> bool:
    """Check that (1) model_quant has Quant* layers, (2) logits differ, (3) for bw<32 some predictions differ from baseline."""
    model_baseline.eval()
    model_quant.eval()
    n_quant = sum(
        1 for m in model_quant.modules()
        if isinstance(m, (QuantLinear, QuantConv2d))
    )
    if n_quant == 0:
        print(f"  [WARN] PTQ verification: no QuantLinear/QuantConv2d in model (bit_width={bit_width})")
        return False
    for m in model_quant.modules():
        if isinstance(m, (QuantLinear, QuantConv2d)) and getattr(m, "bit_width", None) != bit_width:
            print(f"  [WARN] PTQ verification: found Quant layer with bit_width={getattr(m,'bit_width')} != {bit_width}")
            break
    else:
        pass  # all have correct bit_width

    num_diff_pred = 0
    num_total = 0
    logits_max_diff = 0.0
    with torch.no_grad():
        for bi, (x, _) in enumerate(test_loader):
            if bi >= num_batches_check:
                break
            x = x.to(device)
            logits_base = model_baseline(x)
            logits_quant = model_quant(x)
            logits_max_diff = max(logits_max_diff, (logits_quant - logits_base).abs().max().item())
            pred_base = logits_base.argmax(dim=1)
            pred_quant = logits_quant.argmax(dim=1)
            num_diff_pred += (pred_base != pred_quant).sum().item()
            num_total += pred_base.numel()
    if bit_width < 32 and logits_max_diff < 1e-5:
        print(f"  [WARN] PTQ verification: bit_width={bit_width} but logits match baseline (max_diff={logits_max_diff}). Quantization may not be applied in forward.")
        return False
    if bit_width < 32 and num_diff_pred == 0:
        print(f"  [WARN] PTQ verification: bit_width={bit_width} but 0/{num_total} predictions differ from baseline over {num_batches_check} batches. Try --max-eval-batches 0 for full test set.")
    return True


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def evaluate_vision(model: nn.Module, test_loader: DataLoader, max_batches: int | None = None, device=None):
    model.eval()
    if device is None:
        device = next(model.parameters()).device
    total, correct = 0, 0
    with torch.no_grad():
        for i, (x, y) in enumerate(test_loader):
            if max_batches is not None and i >= max_batches:
                break
            x, y = x.to(device), y.to(device)
            logits = model(x)
            pred = logits.argmax(dim=1)
            correct += (pred == y).sum().item()
            total += y.size(0)
    return correct / total if total else 0.0


def evaluate_nlp(model: nn.Module, test_loader: DataLoader, max_batches: int | None = None, device=None):
    """Accuracy on tokenized IMDB test set."""
    model.eval()
    if device is None:
        device = next(model.parameters()).device
    total, correct = 0, 0
    with torch.no_grad():
        for i, batch in enumerate(test_loader):
            if max_batches is not None and i >= max_batches:
                break
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch)
            pred = out.logits.argmax(dim=1)
            correct += (pred == batch["labels"]).sum().item()
            total += batch["labels"].size(0)
    return correct / total if total else 0.0


# ---------------------------------------------------------------------------
# Result saving
# ---------------------------------------------------------------------------

def save_result(result: dict, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_slug = result["model"].replace(" ", "_").replace("-", "_").lower()
    fname = f"{model_slug}_w{result['bit_width']}_{ts}.json"
    path = os.path.join(output_dir, fname)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  -> Saved: {path}")


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------

def run_sweep(
    model_names: list[str] | None,
    bit_widths: list[int],
    run_qat: bool,
    qat_epochs: int,
    output_dir: str,
    batch_size: int,
    max_eval_batches: int,
    train_epochs: int = 0,
    save_checkpoint_dir: str | None = None,
    qat_lr: float | None = None,
    force_train: bool = False,
):
    supported = [c for c in MODEL_CONFIGS if c.name in ("ResNet18", "ResNet50", "BERT-tiny")]
    if model_names:
        configs = [c for c in supported if c.name in model_names]
    else:
        configs = supported
    if not configs:
        print("No matching models. Use --models ResNet18 ResNet50 \"BERT-tiny\"")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    eval_batches = None if max_eval_batches == 0 else max_eval_batches  # 0 = full test set
    # CIFAR-10 loaders for vision (only if any vision model)
    vision_configs = [c for c in configs if not c.is_nlp]
    if vision_configs:
        train_loader_v, val_loader_v, test_loader_v = get_cifar10_dataloaders(batch_size=batch_size)

    for cfg in configs:
        effective_dataset = cfg.dataset.strip().lower()
        print(f"\n{'='*70}")
        print(f"Model: {cfg.name}  |  Dataset: {effective_dataset}  |  Layers: {cfg.layer_types}")
        print(f"{'='*70}")

        try:
            if cfg.is_nlp:
                # ------ NLP: BERT-tiny on IMDB ------
                train_loader, val_loader, test_loader, _ = get_imdb_dataloaders(cfg, batch_size=batch_size)
                model = load_nlp_model(cfg).to(device)
            else:
                train_loader, val_loader, test_loader = train_loader_v, val_loader_v, test_loader_v
                model = load_vision_model(cfg, num_classes=10).to(device)

            # ------ Load trained checkpoint if present (unless --force-train) ------
            loaded_trained_ckpt = False
            if save_checkpoint_dir and not force_train:
                ckpt_name = cfg.name.replace(" ", "_").replace("-", "_") + "_trained.pt"
                ckpt_path = os.path.join(save_checkpoint_dir, ckpt_name)
                if os.path.isfile(ckpt_path):
                    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
                    if cfg.is_nlp:
                        target_keys = set(model.state_dict().keys())
                        state = {k: v for k, v in state.items() if k in target_keys}
                    model.load_state_dict(state, strict=not cfg.is_nlp)
                    loaded_trained_ckpt = True
                    print(f"\n[Checkpoint] Loaded trained weights from {ckpt_path}")

            # ------ Train baseline (optional) ------
            if train_epochs > 0 and not loaded_trained_ckpt:
                print(f"\n[Train] Training baseline on {effective_dataset} for {train_epochs} epoch(s)...")
                t0 = time.time()
                if cfg.is_nlp:
                    wrapper = NLPWrapper(model, lr=2e-5)
                else:
                    wrapper = VisionWrapper(model, lr=1e-3)
                trainer = pl.Trainer(
                    accelerator="auto",
                    devices=1,
                    max_epochs=train_epochs,
                    enable_progress_bar=True,
                    logger=False,
                )
                trainer.fit(wrapper, train_dataloaders=train_loader, val_dataloaders=val_loader)
                print(f"  Training done ({time.time() - t0:.1f}s)")

            # ------ Save trained baseline ------
            if save_checkpoint_dir and (train_epochs > 0 and not loaded_trained_ckpt):
                os.makedirs(save_checkpoint_dir, exist_ok=True)
                ckpt_name = cfg.name.replace(" ", "_").replace("-", "_") + "_trained.pt"
                ckpt_path = os.path.join(save_checkpoint_dir, ckpt_name)
                torch.save(model.state_dict(), ckpt_path)
                print(f"  Saved checkpoint: {ckpt_path}")

            # ------ Baseline evaluation ------
            print("\n[Baseline] Evaluating full-precision model...")
            # After Lightning training, weights may be on CPU; ensure model and inputs share the same device.
            model.to(device)
            t0 = time.time()
            if cfg.is_nlp:
                baseline_acc = evaluate_nlp(model, test_loader, max_batches=eval_batches, device=device)
            else:
                baseline_acc = evaluate_vision(model, test_loader, max_batches=eval_batches, device=device)
            print(f"  Baseline accuracy: {baseline_acc}  ({time.time() - t0:.1f}s)")

            # ------ Bit-width sweep: PTQ + optional QAT ------
            for bw in bit_widths:
                print(f"\n[PTQ] bit_width={bw}, layers={cfg.layer_types}")
                if cfg.is_nlp:
                    model_bw = load_nlp_model(cfg).to(device)
                    state = model.state_dict()
                    target_keys = set(model_bw.state_dict().keys())
                    state = {k: v for k, v in state.items() if k in target_keys}
                    model_bw.load_state_dict(state, strict=False)
                else:
                    model_bw = load_vision_model(cfg, num_classes=10).to(device)
                    model_bw.load_state_dict(model.state_dict(), strict=True)
                replace_with_quant(model_bw, bit_width=bw, layer_types=cfg.layer_types)

                if not cfg.is_nlp:
                    _verify_ptq_vision(model, model_bw, test_loader, bw, device)

                t0 = time.time()
                if cfg.is_nlp:
                    ptq_acc = evaluate_nlp(model_bw, test_loader, max_batches=eval_batches, device=device)
                else:
                    ptq_acc = evaluate_vision(model_bw, test_loader, max_batches=eval_batches, device=device)
                print(f"  PTQ accuracy: {ptq_acc}  ({time.time() - t0:.1f}s)")

                qat_acc = None
                if run_qat:
                    qat_lr = qat_lr if qat_lr is not None else (2e-5 if cfg.is_nlp else 1e-3)
                    print(f"  [QAT] Training for {qat_epochs} epoch(s), lr={qat_lr}...")
                    t0 = time.time()
                    if cfg.is_nlp:
                        wrapper_q = NLPWrapper(model_bw, lr=qat_lr)
                    else:
                        wrapper_q = VisionWrapper(model_bw, lr=qat_lr)
                    trainer_q = pl.Trainer(
                        accelerator="auto",
                        devices=1,
                        max_epochs=qat_epochs,
                        enable_progress_bar=True,
                        logger=False,
                    )
                    trainer_q.fit(wrapper_q, train_dataloaders=train_loader, val_dataloaders=val_loader)
                    model_bw.to(device)
                    if cfg.is_nlp:
                        qat_acc = evaluate_nlp(model_bw, test_loader, max_batches=eval_batches, device=device)
                    else:
                        qat_acc = evaluate_vision(model_bw, test_loader, max_batches=eval_batches, device=device)
                    print(f"  QAT accuracy: {qat_acc}  ({time.time() - t0:.1f}s)")
                    if save_checkpoint_dir:
                        os.makedirs(save_checkpoint_dir, exist_ok=True)
                        safe_name = cfg.name.replace(" ", "_").replace("-", "_")
                        qat_ckpt = os.path.join(save_checkpoint_dir, f"{safe_name}_w{bw}_qat.pt")
                        torch.save(model_bw.state_dict(), qat_ckpt)
                        print(f"  Saved QAT checkpoint: {qat_ckpt}")

                result = {
                    "model": cfg.name,
                    "checkpoint": cfg.checkpoint,
                    "dataset": effective_dataset,
                    "layer_types": cfg.layer_types,
                    "bit_width": bw,
                    "frac_width": bw // 2,
                    "scheme": "integer",
                    "baseline_accuracy": baseline_acc,
                    "ptq_accuracy": ptq_acc,
                    "qat_accuracy": qat_acc,
                    "train_epochs": train_epochs,
                    "qat_epochs": qat_epochs if run_qat else 0,
                    "timestamp": datetime.now().isoformat(),
                }
                save_result(result, output_dir)

        except Exception as e:
            print(f"  ERROR processing {cfg.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\nSweep complete. Results saved to: {output_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Quantization sweep (ResNet18/50 + BERT-tiny)"
    )
    parser.add_argument(
        "--models", nargs="*", default=None,
        help='Model names: ResNet18, ResNet50, "BERT-tiny" (default: all)',
    )
    parser.add_argument(
        "--bit-widths", nargs="*", type=int, default=BIT_WIDTHS,
        help=f"Bit-widths to sweep (default: {BIT_WIDTHS})",
    )
    parser.add_argument("--run-qat", action="store_true", help="Run QAT after PTQ")
    parser.add_argument("--qat-epochs", type=int, default=1, help="Number of QAT epochs")
    parser.add_argument("--qat-lr", type=float, default=None, help="QAT learning rate (default: 2e-5 NLP, 1e-3 vision). Try 1e-5 if QAT accuracy drops.")
    parser.add_argument(
        "--output-dir", type=str,
        default=str(Path(__file__).parent / "results"),
        help="Directory to save results",
    )
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-eval-batches", type=int, default=0,
                        help="Max batches for eval (0 = full test set; use e.g. 200 for quick runs)")
    parser.add_argument("--train-epochs", type=int, default=0, help="Train baseline for N epochs first")
    parser.add_argument("--save-checkpoint-dir", type=str, default=None)
    parser.add_argument("--force-train", action="store_true",
                        help="Ignore existing baseline checkpoint and always train for --train-epochs")
    args = parser.parse_args()

    run_sweep(
        model_names=args.models,
        bit_widths=args.bit_widths,
        run_qat=args.run_qat,
        qat_epochs=args.qat_epochs,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        max_eval_batches=args.max_eval_batches,
        train_epochs=args.train_epochs,
        save_checkpoint_dir=args.save_checkpoint_dir,
        qat_lr=args.qat_lr,
        force_train=args.force_train,
    )


if __name__ == "__main__":
    main()
