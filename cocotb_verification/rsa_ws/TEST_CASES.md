# RSA-WS Simulation Test Cases

The cocotb regression in this directory is `matrix_axi_wrapper_tb.py`, which verifies the runtime-configurable `matrix_top_wrapper`.

Compared with the fixed WS version, this regression checks not only GEMM correctness but also:

- Whether auto-configuration selects the expected array shape.
- Whether manual row and column masks are applied correctly.
- Whether configuration status registers report the selected setup correctly.
- Whether B-tile reuse is preserved.

## Basic Auto Cases

- `smoke_dense_auto`
  Standard `8x8x8` dense case. Verifies default auto mode behavior.
- `odd_sizes_auto`
  `5x11x7`. Verifies non-exact tiling in auto mode.
- `zero_m_auto`
  `M=0`. Verifies zero-dimension fast exit.
- `zero_k_auto`
  `K=0`. Verifies zero-dimension fast exit.
- `zero_n_auto`
  `N=0`. Verifies zero-dimension fast exit.
- `max_values_auto`
  Positive numeric stress case in auto mode.
- `min_values_auto`
  Negative numeric stress case in auto mode.

## Manual Configuration Cases

- `manual_sparse_bypass`
  Uses `row_mask=0x55` and `col_mask=0x33`. Verifies sparse non-contiguous PE masking.
- `manual_zero_mask_fallback`
  Writes zero masks intentionally and verifies fallback to full-enable masks instead of an invalid empty array.

These cases also verify:

- `cfg_id`
- `active_rows`
- `active_cols`
- `row_mask`
- `col_mask`

## Auto Selection Cases

- `auto_balanced_4x4`
  Verifies automatic selection of the `4x4` configuration.
- `auto_tall_4x8`
  Verifies automatic selection of the `4x8` configuration.
- `auto_wide_8x4`
  Verifies automatic selection of the `8x4` configuration.
- `auto_small_2x2`
  Verifies automatic selection of the `2x2` configuration.

## Repeat Cases

- `repeat_manual_same_output_base`
  First run uses a manual `4x8` configuration on a fixed output base.
- `repeat_auto_same_output_base`
  Second run uses an auto-selected `4x4` configuration on the same output base.

These cases verify that:

- Switching between manual and auto mode does not leave stale configuration state behind.
- Reusing the same `baseC` does not leave stale output data behind.

## Reuse Case

- `manual_4x8_b_reuse`
  Verifies that B-tile reuse is preserved under a manual `4x8` configuration.

This case also checks:

- `B_reads` matches the expected reuse behavior.
- `C_writes` equals `M*N`.

## Main Checks

- Every normal case must produce a C matrix that matches the golden GEMM result.
- Zero-dimension cases must not modify the output region.
- Guard words after the valid C region must remain unchanged.
- After completion, the status register must report `busy=0, done=1`.
- Configuration status register `0x30` and mask register `0x34` must match the expected selected configuration.
