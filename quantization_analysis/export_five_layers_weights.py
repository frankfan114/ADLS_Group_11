#!/usr/bin/env python3
"""
Export weights of 5 FC layers to JSON as integers. Each layer is from a *specific* quantized (QAT) model.
See per_layer_results/FIVE_LAYERS_FROM_QUANTIZED_MODELS.md for why each (checkpoint, layer) was chosen.
Output: per_layer_results/weights/<out_name>.json
"""

import json
from pathlib import Path

import torch


# Five (quantized checkpoint, layer) pairs: each from a different QAT variant. One checkpoint file per row.
# out_name used for JSON filename; source_checkpoint written into JSON.
FIVE_LAYERS_FROM_QUANTIZED = [
    {"source_checkpoint": "ResNet18_w4_qat.pt", "layer_id": "ResNet18#L0#fc", "weight_key": "fc.weight", "bias_key": "fc.bias", "out_name": "resnet18_w4_fc_weights", "reason": "4-bit CNN classifier; small 10x512, high sensitivity"},
    {"source_checkpoint": "ResNet50_w8_qat.pt", "layer_id": "ResNet50#L0#fc", "weight_key": "fc.weight", "bias_key": "fc.bias", "out_name": "resnet50_w8_fc_weights", "reason": "8-bit large CNN classifier 10x2048; mid-bit deployment"},
    {"source_checkpoint": "BERT_tiny_w4_qat.pt", "layer_id": "BERT-tiny#L3#bert.encoder.layer.0.attention.self.query", "weight_key": "bert.encoder.layer.0.attention.self.query.weight", "bias_key": "bert.encoder.layer.0.attention.self.query.bias", "out_name": "bert_tiny_w4_attention_self_query_layer0_weights", "reason": "4-bit attention Q 128x128; very high sensitivity"},
    {"source_checkpoint": "BERT_tiny_w8_qat.pt", "layer_id": "BERT-tiny#L7#bert.encoder.layer.0.intermediate.dense", "weight_key": "bert.encoder.layer.0.intermediate.dense.weight", "bias_key": "bert.encoder.layer.0.intermediate.dense.bias", "out_name": "bert_tiny_w8_intermediate_dense_layer0_weights", "reason": "8-bit FFN 512x128; low sensitivity, large matrix"},
    {"source_checkpoint": "BERT_tiny_w32_qat.pt", "layer_id": "BERT-tiny#L16#classifier", "weight_key": "classifier.weight", "bias_key": "classifier.bias", "out_name": "bert_tiny_w32_classifier_weights", "reason": "32-bit tiny classifier 2x128; near full-precision control"},
]

SCRIPT_DIR = Path(__file__).resolve().parent
CHECKPOINT_DIR = SCRIPT_DIR / "checkpoints"
OUTPUT_DIR = SCRIPT_DIR / "per_layer_results" / "weights"


def float_to_int_tensor(t: torch.Tensor, bit_width: int = 8) -> tuple[list, float]:
    """Symmetric quantization to signed int. Returns (int_list, scale_for_dequant)."""
    t = t.detach().cpu().float()
    half = 2 ** (bit_width - 1)
    max_val = half - 1  # e.g. 127 for 8-bit
    max_abs = t.abs().max().item()
    if max_abs < 1e-9:
        scale_dequant = 1.0
        t_int = torch.zeros_like(t, dtype=torch.long)
    else:
        scale_quant = max_val / max_abs
        t_int = torch.round(t * scale_quant).clamp(-half, half - 1).long()
        scale_dequant = max_abs / max_val
    return t_int.tolist(), scale_dequant


def export_layer(ckpt_path: Path, layer_spec: dict, out_path: Path, bit_width: int = 8, source_ckpt_name: str = ""):
    state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
    weight_key = layer_spec["weight_key"]
    bias_key = layer_spec["bias_key"]
    if weight_key not in state:
        raise KeyError(f"Missing {weight_key} in {ckpt_path}")
    w = state[weight_key]
    b = state.get(bias_key)
    weight_int, scale_weight = float_to_int_tensor(w, bit_width)
    out = {
        "layer_id": layer_spec["layer_id"],
        "source_checkpoint": source_ckpt_name,
        "weight_shape": list(w.shape),
        "weight": weight_int,
        "scale_weight": scale_weight,
        "bias": None,
        "scale_bias": None,
    }
    if b is not None:
        bias_int, scale_bias = float_to_int_tensor(b, bit_width)
        out["bias"] = bias_int
        out["scale_bias"] = scale_bias
    out["export_bit_width"] = bit_width
    out["note"] = "int values; to recover float: float_val = int_val * scale_*"
    if layer_spec.get("reason"):
        out["reason"] = layer_spec["reason"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Saved {out_path} (shape {out['weight_shape']}, int{bit_width})")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Export 5 FC layers' weights as integers; each from a specific QAT checkpoint (see FIVE_LAYERS_FROM_QUANTIZED)")
    p.add_argument("--bits", type=int, default=8, help="Export integer bit width for JSON (8 or 16, default 8)")
    args = p.parse_args()
    bit_width = max(2, min(16, args.bits))

    if not CHECKPOINT_DIR.is_dir():
        print(f"Checkpoint dir not found: {CHECKPOINT_DIR}")
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in FIVE_LAYERS_FROM_QUANTIZED:
        ckpt_name = spec["source_checkpoint"]
        ckpt_path = CHECKPOINT_DIR / ckpt_name
        if not ckpt_path.is_file():
            print(f"Skip {spec['layer_id']}: {ckpt_path} not found")
            continue
        print(f"Loading {ckpt_path} -> {spec['out_name']}")
        out_path = OUTPUT_DIR / f"{spec['out_name']}.json"
        export_layer(ckpt_path, spec, out_path, bit_width=bit_width, source_ckpt_name=ckpt_name)
    print(f"\nDone. Weights in {OUTPUT_DIR} (int{bit_width})")


if __name__ == "__main__":
    main()
