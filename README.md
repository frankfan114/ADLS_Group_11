# ADL Group 11 - Layer Info & Quantization Analysis

This branch (`layer_info`) contains per-layer profiling, quantization experiments, and selected layer exports for hardware accelerator design.

## Directory Structure

```
experiments/quantization_analysis/
├── configs.py                    # Model configs (ResNet18/50, BERT-tiny)
├── quant_layers.py               # QuantLinear / QuantConv2d, replace_with_quant
├── run_sweep.py                  # Train baseline + PTQ/QAT sweep
├── per_layer_profile.py          # Per-layer weight/activation/sensitivity profiling
├── export_five_layers_weights.py # Export 5 selected layers' int weights to JSON
├── export_sparsest_two_layers.py # Export the two sparsest conv layers
├── quantize_yolov8n_qat.py       # YOLOv8n QAT script
├── analyze_per_layer_results.py  # Analysis helpers
├── per_layer_results/            # JSON profiles + selected layer exports
└── results/                      # Sweep metrics per model × bit-width
```

## Selected Layers

Five (model, layer) pairs were chosen from QAT checkpoints to cover different hardware design scenarios:

| # | Checkpoint | Layer | Shape | Purpose |
|---|-----------|-------|-------|---------|
| 1 | ResNet18_w4_qat | `fc` | [10, 512] | Low-bit CNN classifier head |
| 2 | ResNet50_w8_qat | `fc` | [10, 2048] | Mid-bit large CNN classifier |
| 3 | BERT-tiny_w4_qat | `encoder.layer.0.attention.self.query` | [128, 128] | Low-bit Transformer attention |
| 4 | BERT-tiny_w8_qat | `encoder.layer.0.intermediate.dense` | [512, 128] | Mid-bit large FFN |
| 5 | BERT-tiny_w32_qat | `classifier` | [2, 128] | Full-precision tiny task head |

See [`per_layer_results/FIVE_LAYERS_FROM_QUANTIZED_MODELS.md`](experiments/quantization_analysis/per_layer_results/FIVE_LAYERS_FROM_QUANTIZED_MODELS.md) for full rationale.

## Quick Start

```bash
# 1. Train + PTQ/QAT sweep
python run_sweep.py --models ResNet18 ResNet50 "BERT-tiny" \
  --bit-widths 4 8 16 32 --train-epochs 10 --run-qat --qat-epochs 3 \
  --save-checkpoint-dir checkpoints

# 2. Per-layer profile (weights, activation sparsity, sensitivity)
python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" \
  --checkpoint-dir checkpoints --calibration-batches 8 \
  --sensitivity --profile-quantized

# 3. Export selected 5 layers' int weights
python export_five_layers_weights.py
```

## Models

- **ResNet18 / ResNet50** — image classification (CIFAR-10), FC + Conv2d layers profiled
- **BERT-tiny** — text classification, Linear layers profiled
- **YOLOv8n** — object detection, int8 conv layer export
