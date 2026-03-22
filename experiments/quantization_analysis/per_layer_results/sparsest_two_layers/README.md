# Two sparsest layers (by activation) — metadata and weights

- **Layer name:** `layer4.1.conv3` (third 1×1 conv in a ResNet50 bottleneck block).
- **Source:** The two entries with the highest `activation_sparsity_zero` across `per_layer_results` (w4 QAT and w16 QAT checkpoints).

| File | Description |
|------|-------------|
| `sparsest_two_layers_info.json` | Full per-layer profile fields (from `*_conv_per_layer.json`) plus source filenames. |
| `resnet50_w4_layer4_1_conv3_weights.json` | Weights from `ResNet50_w4_qat.pt` (int8 list + `scale_weight`). |
| `resnet50_w16_layer4_1_conv3_weights.json` | Weights from `ResNet50_w16_qat.pt` (same format). |

Weight JSON files are large (~1M parameters as nested int lists). Regenerate with:

```bash
cd experiments/quantization_analysis
python export_sparsest_two_layers.py
```

Requires matching `*.pt` files under `checkpoints/`.
