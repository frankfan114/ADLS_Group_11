# 最稀疏两层（activation）— 信息与权重

- **层名：** `layer4.1.conv3`（ResNet50 bottleneck 第 3 个 1×1 conv）
- **来源：** 全库 `per_layer_results` 中 `activation_sparsity_zero` 最高的两条记录（w4 QAT 与 w16 QAT）

| 文件 | 说明 |
|------|------|
| `sparsest_two_layers_info.json` | 两层完整 profile 字段（来自 `*_conv_per_layer.json`）+ 来源文件名 |
| `resnet50_w4_layer4_1_conv3_weights.json` | 从 `ResNet50_w4_qat.pt` 导出的权重（int8 + scale） |
| `resnet50_w16_layer4_1_conv3_weights.json` | 从 `ResNet50_w16_qat.pt` 导出 |

权重 JSON 体积较大（约 1M 参数 × 整型列表）。重新生成：

```bash
python export_sparsest_two_layers.py
```

（在 `quantization_analysis` 目录下，`checkpoints/` 需存在对应 `.pt`。）
