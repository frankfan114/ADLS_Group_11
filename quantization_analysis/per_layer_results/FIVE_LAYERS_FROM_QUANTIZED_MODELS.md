# Five Layers Selected from Quantized Models (QAT)

From the **three base models** (ResNet18, ResNet50, BERT-tiny) and their **QAT checkpoints** (w4, w8, w16, w32), the following **5 (quantized model, layer)** pairs were chosen. Each layer is tied to **one specific quantized checkpoint** and has a clear reason for selection.

---

## The Five Selections

| # | Quantized model (checkpoint) | Layer name | weight_shape | Why this layer from this quantized model |
|---|------------------------------|------------|--------------|------------------------------------------|
| 1 | **ResNet18_w4_qat.pt** | fc | [10, 512] | 4-bit is the most aggressive QAT for this model; the single FC is sensitivity-critical (drop ≈ 0.55 at 2-bit). Represents **low-bit CNN classifier head** for hardware that targets strong compression. |
| 2 | **ResNet50_w8_qat.pt** | fc | [10, 2048] | 8-bit is a common deployment choice; ResNet50’s fc is 4× larger than ResNet18’s (10×2048). Represents **mid-bit large CNN classifier** and stresses bandwidth/compute for a single GEMM. |
| 3 | **BERT_tiny_w4_qat.pt** | bert.encoder.layer.0.attention.self.query | [128, 128] | 4-bit QAT on the most sensitivity-critical layer in the profile (drop ≈ 0.74). Represents **low-bit Transformer attention** and motivates mixed-precision or higher bit for attention in hardware. |
| 4 | **BERT_tiny_w8_qat.pt** | bert.encoder.layer.0.intermediate.dense | [512, 128] | 8-bit QAT on the large FFN expansion (65K params); this layer is quantization-tolerant (drop ≈ -0.08). Represents **mid-bit large FFN** where aggressive quantization is safe. |
| 5 | **BERT_tiny_w32_qat.pt** | classifier | [2, 128] | 32-bit QAT is effectively full-precision; the classifier is tiny (256 params) and has negligible sensitivity. Represents **high-bit tiny task head** as a control or for minimal-precision datapath design. |

---

## Summary: Coverage

- **Models:** ResNet18 (1 layer), ResNet50 (1 layer), BERT-tiny (3 layers).
- **QAT bit widths:** w4 (2), w8 (2), w32 (1) — so low-, mid-, and high-precision QAT are all represented.
- **Layer roles:** CNN classifier (×2), attention Q, FFN expansion, task classifier.
- **Reasons:** Each choice is tied to a specific quantized model and explains why that (checkpoint, layer) pair is useful for hardware or analysis.

---

## Exporting these five layers

Run:

```bash
python export_five_layers_weights.py
```

This uses the list `FIVE_LAYERS_FROM_QUANTIZED` in `export_five_layers_weights.py`: each of the 5 layers is read from its **own** checkpoint (ResNet18_w4_qat.pt, ResNet50_w8_qat.pt, BERT_tiny_w4_qat.pt, BERT_tiny_w8_qat.pt, BERT_tiny_w32_qat.pt). Output JSONs are written to `per_layer_results/weights/` with names that include the source QAT variant (e.g. `resnet18_w4_fc_weights.json`).
