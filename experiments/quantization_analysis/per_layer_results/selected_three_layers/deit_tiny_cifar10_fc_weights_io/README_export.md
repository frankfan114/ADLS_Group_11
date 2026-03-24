# DeiT-tiny CIFAR-10 classifier head export

## Source model (Hugging Face)

- **Default:** `fancifulcrow/deit-tiny-patch16-224-finetuned-cifar10`
- **Head:** `classifier` — Linear **192 → 10** (`embed_dim=192`)

## Quantization convention (same spirit as ResNet18 fc export)

| Tensor   | Role        | Bit-width |
|----------|-------------|-----------|
| Input X  | Activations | **int8**  |
| Weight W |             | **int4** ([-8, 7]) |
| Bias b   |             | **int4** ([-8, 7]) |
| Output Y | Golden      | **int8** (symmetric requant of `int64(X @ Wᵀ + b)` over full acc) |

- **Raw JSON** (`*_io_raw_nobias_noscale.json`): full tensors, no separate scale fields in the arrays.
- **Bias** is also in `case0_bias_deit_tiny_cifar10_fc.vh`; golden **OUT** already includes bias + requant.

## Files

| File | Description |
|------|-------------|
| `deit_tiny_cifar10_fc_weights_io_raw_nobias_noscale.json` | input / weight / bias / output (raw ints) |
| `deit_tiny_cifar10_fc_weights_io.json` | int8 I/O + scales (snapshot) |
| `deit_tiny_cifar10_fc_weights.json` | weights + bias + scales |
| `deit_tiny_cifar10_fc_weights_raw_nobias_noscale.json` | weight + bias only |
| `deit_tiny_cifar10_fc_weights_info.json` | layer info + stats |
| `case0_json_data_deit_tiny_cifar10_fc_raw.vh` | A, B, OUT init for Verilog TB |
| `case0_bias_deit_tiny_cifar10_fc.vh` | per-class bias |

## Regenerate

```bash
cd experiments/quantization_analysis
python export_deit_tiny_fc_cifar10_from_hf.py
# optional: --model-id <hf_id> --batch-size 64 --out-dir ...
```

Requires: `pip install transformers`

## TB dimensions (case 0)

- `CASE0_M_DIM = 64` (batch size)
- `CASE0_K_DIM = 192`
- `CASE0_N_DIM = 10`

Adjust if you change `--batch-size`.
