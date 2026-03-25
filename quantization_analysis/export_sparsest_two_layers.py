#!/usr/bin/env python3
"""
Extract profile + weights for the two sparsest conv layers (by activation sparsity in per_layer_results):
  - ResNet50 layer4.1.conv3 @ w4 QAT
  - ResNet50 layer4.1.conv3 @ w16 QAT

Writes:
  per_layer_results/sparsest_two_layers/sparsest_two_layers_info.json
  per_layer_results/sparsest_two_layers/resnet50_w4_layer4_1_conv3_weights.json
  per_layer_results/sparsest_two_layers/resnet50_w16_layer4_1_conv3_weights.json
"""

from __future__ import annotations

import json
from pathlib import Path

import torch

SCRIPT_DIR = Path(__file__).resolve().parent
PROFILE_DIR = SCRIPT_DIR / "per_layer_results"
CHECKPOINT_DIR = SCRIPT_DIR / "checkpoints"
OUT_DIR = PROFILE_DIR / "sparsest_two_layers"

LAYER_NAME = "layer4.1.conv3"

# (profile_json_name, checkpoint_name, export_stem)
SPECS = [
    ("resnet50_w4_qat_conv_per_layer.json", "ResNet50_w4_qat.pt", "resnet50_w4_layer4_1_conv3_weights"),
    ("resnet50_w16_qat_conv_per_layer.json", "ResNet50_w16_qat.pt", "resnet50_w16_layer4_1_conv3_weights"),
]


def float_to_int_tensor(t: torch.Tensor, bit_width: int = 8) -> tuple[list, float]:
    t = t.detach().cpu().float()
    half = 2 ** (bit_width - 1)
    max_val = half - 1
    max_abs = t.abs().max().item()
    if max_abs < 1e-9:
        scale_dequant = 1.0
        t_int = torch.zeros_like(t, dtype=torch.long)
    else:
        scale_quant = max_val / max_abs
        t_int = torch.round(t * scale_quant).clamp(-half, half - 1).long()
        scale_dequant = max_abs / max_val
    return t_int.tolist(), scale_dequant


def find_layer_record(profile_path: Path) -> dict:
    d = json.loads(profile_path.read_text(encoding="utf-8"))
    for rec in d.get("conv_layers", []):
        if rec.get("name") == LAYER_NAME:
            return rec
    raise KeyError(f"No layer named {LAYER_NAME!r} in {profile_path}")


def resolve_weight_keys(state: dict) -> tuple[str, str | None]:
    """QuantConv2d checkpoints use *_conv.weight; plain Conv2d uses .weight."""
    candidates_w = [
        f"{LAYER_NAME}._conv.weight",
        f"{LAYER_NAME}.weight",
    ]
    candidates_b = [
        f"{LAYER_NAME}._conv.bias",
        f"{LAYER_NAME}.bias",
    ]
    wk = next((k for k in candidates_w if k in state), None)
    if wk is None:
        raise KeyError(f"No weight key in {candidates_w}; sample keys: {list(state.keys())[:8]}...")
    bk = next((k for k in candidates_b if k in state), None)
    return wk, bk


def export_weights(ckpt_path: Path, out_path: Path, layer_record: dict, source_ckpt: str, bit_width: int = 8):
    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    wk, bk = resolve_weight_keys(state)
    w = state[wk]
    b = state.get(bk) if bk else None

    weight_int, scale_w = float_to_int_tensor(w, bit_width)
    out = {
        "layer_name": LAYER_NAME,
        "layer_id": layer_record.get("layer_id"),
        "source_checkpoint": source_ckpt,
        "state_dict_weight_key": wk,
        "state_dict_bias_key": bk,
        "weight_shape": list(w.shape),
        "weight": weight_int,
        "scale_weight": scale_w,
        "bias": None,
        "scale_bias": None,
        "export_bit_width": bit_width,
        "note": "int values; float ≈ int * scale. 4D conv weight nested list [out_c][in_c][kH][kW].",
    }
    if b is not None:
        bi, scale_b = float_to_int_tensor(b, bit_width)
        out["bias"] = bi
        out["scale_bias"] = scale_b

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"  Saved {out_path} (shape {out['weight_shape']})")


def main():
    bit_width = 8
    layers_info = []
    for prof_name, ckpt_name, stem in SPECS:
        prof_path = PROFILE_DIR / prof_name
        ckpt_path = CHECKPOINT_DIR / ckpt_name
        if not prof_path.is_file():
            print(f"Skip: profile not found {prof_path}")
            continue
        if not ckpt_path.is_file():
            print(f"Skip: checkpoint not found {ckpt_path}")
            continue

        rec = find_layer_record(prof_path)
        layers_info.append(
            {
                "profile_source": prof_name,
                "checkpoint": ckpt_name,
                "layer_name": LAYER_NAME,
                "rank_note": "Among all per_layer_results profiles, highest activation_sparsity_zero (calibration).",
                "profile_layer": rec,
            }
        )

        out_w = OUT_DIR / f"{stem}.json"
        export_weights(ckpt_path, out_w, rec, ckpt_name, bit_width=bit_width)

    manifest = {
        "title": "Two sparsest layers (activation sparsity) + exported weights",
        "layer": LAYER_NAME,
        "model": "ResNet50",
        "layers": layers_info,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "sparsest_two_layers_info.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n  Wrote {OUT_DIR / 'sparsest_two_layers_info.json'}")
    print(f"Done. Output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
