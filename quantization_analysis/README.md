# Quantization Analysis Folder Guide

This folder contains the full quantization workflow used in this project:
training/quantization sweeps, per-layer profiling, layer selection, and hardware-ready exports.

## 1) Folder structure (including subfolders)

```text
quantization_analysis/
├─ README.md
├─ analysis.ipynb
├─ configs.py
├─ quant_layers.py
├─ run_sweep.py
├─ per_layer_profile.py
├─ export_five_layers_weights.py
├─ export_sparsest_two_layers.py
├─ quantize_yolov8n_qat.py
├─ results/
│  ├─ *.json
│  └─ PTQ_EVAL_NOTE.md
└─ per_layer_results/
   ├─ *.json                          # per-model/per-bit-width layer profiles
   ├─ FIVE_LAYERS_FROM_QUANTIZED_MODELS.md
   ├─ _scan_sparsity.py
   ├─ weights/
   │  └─ *.json                       # exported selected layer weights
   ├─ sparsest_two_layers/
   │  ├─ README.md
   │  ├─ sparsest_two_layers_info.json
   │  └─ *.json
   └─ selected_three_layers/
      ├─ bert_tiny_w4_classifier_weights_io/
      ├─ deit_tiny_cifar10_fc_weights_io/
      ├─ mnist_mlp_w8_qat_classifier_weights_io/
      ├─ resnet18_w4_fc_weights_io/
      └─ yolov8n_int8_model_22_cv3_2_2_io/
```

## 2) Top-level files

- `configs.py`: model/task configuration used by sweep/profile scripts.
- `quant_layers.py`: quantized layer implementations (`QuantLinear`, `QuantConv2d`) and replacement helpers.
- `run_sweep.py`: baseline + PTQ + QAT sweep (multiple bit-widths), writes summary JSON into `results/`.
- `per_layer_profile.py`: layer-wise statistics export (weight/activation range, sparsity, sensitivity options).
- `export_five_layers_weights.py`: exports predefined 5 selected layers from quantized checkpoints.
- `export_sparsest_two_layers.py`: exports the two most sparse convolution layers.
- `quantize_yolov8n_qat.py`: YOLOv8n-specific quantization path.
- `analysis.ipynb`: optional plotting/analysis notebook.

## 3) `results/` subfolder

- Stores experiment summaries from `run_sweep.py` (one JSON per model/bit-width run).
- `PTQ_EVAL_NOTE.md` documents PTQ evaluation details and verification notes.

## 4) `per_layer_results/` subfolder

- Root `*.json`: per-layer profiling outputs (linear/conv; baseline and quantized variants).
- `FIVE_LAYERS_FROM_QUANTIZED_MODELS.md`: rationale for the 5 selected quantized layers.
- `_scan_sparsity.py`: helper script for sparsity scanning/selection.

### 4.1 `per_layer_results/weights/`

Contains exported weight JSON for selected layers (from specific checkpoints).

### 4.2 `per_layer_results/sparsest_two_layers/`

Contains:
- selection metadata (`sparsest_two_layers_info.json`),
- exported weights for the two selected sparse conv layers,
- local README with regeneration notes.

### 4.3 `per_layer_results/selected_three_layers/`

Contains hardware-oriented per-layer bundles, each in its own subfolder:
- weight JSON,
- IO JSON,
- raw no-bias/no-scale JSON,
- layer info JSON,
- optional Verilog `.vh` init files for testbench data injection.

Current subfolders include:
- `bert_tiny_w4_classifier_weights_io/`
- `deit_tiny_cifar10_fc_weights_io/`
- `mnist_mlp_w8_qat_classifier_weights_io/`
- `resnet18_w4_fc_weights_io/`
- `yolov8n_int8_model_22_cv3_2_2_io/`

## 5) Common commands

```bash
# 1) Sweep
python run_sweep.py --models ResNet18 ResNet50 "BERT-tiny" --bit-widths 4 8 16 32 --train-epochs 10 --run-qat --qat-epochs 3

# 2) Per-layer profile
python per_layer_profile.py --models ResNet18 ResNet50 "BERT-tiny" --calibration-batches 8 --sensitivity --profile-quantized

# 3) Export selected weights
python export_five_layers_weights.py
python export_sparsest_two_layers.py
```

## 6) Notes

- Activation sparsity metrics are computed from layer forward outputs during calibration.
- BERT-tiny has no Conv2d path in this profiling pipeline (linear layers only).
- Hardware test assets under `selected_three_layers/` are the preferred inputs for RTL simulation.
