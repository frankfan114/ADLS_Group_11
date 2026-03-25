# Quantization analysis

Pure PyTorch: `QuantLinear` / `QuantConv2d`, PTQ/QAT sweep, FC-layer profiling.

**See [WORKFLOW.md](WORKFLOW.md)** for the full pipeline (train → quantize → profile → pick layers → export weights).

## Core scripts

| File                            | Role                                                                               |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| `configs.py`                    | Model configs (ResNet18/50, BERT-tiny, …)                                          |
| `quant_layers.py`               | Quantized layers + `replace_with_quant`                                            |
| `run_sweep.py`                  | Train baseline, PTQ/QAT sweep, save `results/` + `checkpoints/`                    |
| `per_layer_profile.py`          | Linear + Conv2d profiles (`*_linear_*.json`, `*_conv_*.json` for vision)           |
| `export_five_layers_weights.py` | Export 5 selected FC layers’ weights to int JSON from QAT checkpoints              |
| `export_sparsest_two_layers.py` | Export the two sparsest conv layers (see `per_layer_results/sparsest_two_layers/`) |

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

# Quantization experiment workflow

What you use end-to-end:

| Step                              | Purpose                                                                                               | Code                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| 1. Train + PTQ + QAT              | Baseline training, per-bit-width PTQ/QAT, save `results/*.json` and `checkpoints/*.pt`                | `run_sweep.py`                                                                                             |
| 2. Quantization primitives        | `QuantLinear` / `QuantConv2d`, `replace_with_quant`, STE                                              | `quant_layers.py`                                                                                          |
| 3. Model / dataset config         | ResNet18/50, BERT-tiny, layer types                                                                   | `configs.py`                                                                                               |
| 4. Per-layer profile              | Linear + (vision) Conv2d: weight stats, activation (optional), sensitivity (optional), baseline + QAT | `per_layer_profile.py` → `*_linear_per_layer.json`, `*_conv_per_layer.json`                                |
| 5. Pick 5 layers + export weights | Which QAT checkpoint + which layer; int JSON export                                                   | `five_layers_from_quantized.json`, `FIVE_LAYERS_FROM_QUANTIZED_MODELS.md`, `export_five_layers_weights.py` |

**Run examples**

```bash
# Training + sweep (adjust models / epochs)
python run_sweep.py --models ResNet18 ResNet50 "BERT-tiny" --bit-widths 4 8 16 32 --train-epochs 10 --run-qat --qat-epochs 3 --save-checkpoint-dir checkpoints

# FC profile (all info: calibration + sensitivity + quantized profiles)
python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" --checkpoint-dir checkpoints --calibration-batches 8 --sensitivity --profile-quantized

# Export 5 chosen layers’ weights (int JSON) from specific QAT checkpoints
python export_five_layers_weights.py
```

**Outputs**

- `results/` — sweep metrics per model × bit width
- `checkpoints/` — `*_trained.pt`, `*_w*_qat.pt`
- `per_layer_results/` — `*_linear_per_layer.json`, docs, optional `weights/*.json`

**Removed as non-essential** (superseded or optional tooling): `export_five_special_layers_json.py`, `prune_results_keep_latest_per_model.py`.

**Optional:** `analysis.ipynb` — plots/tables from `results/*.json` (not required for training or profiling).
