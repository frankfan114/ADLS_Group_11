# PTQ accuracy and evaluation

- **Why PTQ logits matched baseline (max_diff=0.0) and accuracy was identical:**  
  In `quant_layers._symmetric_quantize` the straight-through estimator (STE) was reversed: the code returned `x_dequant + (x - x_dequant).detach()`, which equals **x** in the forward pass, so the quantized value was never used. **Fix:** return `x + (x_dequant - x).detach()` so that forward output is **x_dequant** (quantized) while gradients still flow as identity.

- **Other changes:**  
  - Default evaluation uses the **full test set** (`--max-eval-batches 0`).  
  - PTQ verification checks that logits and predictions differ from baseline for `bit_width < 32`.

- **Quick run:** Use `--max-eval-batches 200` for faster, subset-based evaluation.
