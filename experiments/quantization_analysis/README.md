# Quantization analysis

Pure PyTorch: `QuantLinear` / `QuantConv2d`, PTQ/QAT sweep, FC-layer profiling.

**See [WORKFLOW.md](WORKFLOW.md)** for the full pipeline (train → quantize → profile → pick layers → export weights).

## Core scripts

| File | Role |
|------|------|
| `configs.py` | Model configs (ResNet18/50, BERT-tiny, …) |
| `quant_layers.py` | Quantized layers + `replace_with_quant` |
| `run_sweep.py` | Train baseline, PTQ/QAT sweep, save `results/` + `checkpoints/` |
| `per_layer_profile.py` | Linear + Conv2d profiles (`*_linear_*.json`, `*_conv_*.json` for vision) |
| `export_five_layers_weights.py` | Export 5 selected layers’ weights to int JSON from QAT checkpoints |

## Quick start

```bash
python run_sweep.py --models ResNet18 --bit-widths 4 8 16 32 --train-epochs 10 --run-qat --qat-epochs 3 --save-checkpoint-dir checkpoints
python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" --checkpoint-dir checkpoints --calibration-batches 8 --sensitivity --profile-quantized
python export_five_layers_weights.py
```

## Optional

- `analysis.ipynb` — load `results/*.json` and plot (optional).

**Activation sparsity (per layer output):** With `--calibration-batches N`, each **Linear** and each **Conv2d** (vision) gets `activation_sparsity_*` on the module’s forward output, same threshold. Root JSON records `activation_near_zero_threshold`.

**Conv2d:** For ResNet18/50, outputs `resnet18_conv_per_layer.json`, `resnet50_w8_qat_conv_per_layer.json`, etc. BERT has no Conv in this pipeline — no conv files. Use `--no-profile-conv` to skip conv JSON and slightly faster calibration.
