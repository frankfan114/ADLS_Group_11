# Weight-Stationary Simulation Test Cases

The cocotb regression in this directory is `matrix_axi_wrapper_tb.py`, which verifies `matrix_top_wrapper`.

The regression is organized around three goals:

- Functional correctness: output values must match the golden GEMM result.
- Robustness and boundary behavior: zero-dimension cases, numeric extremes, partial tiles, and random backpressure.
- Weight-stationary behavior: B-tile reuse should appear in memory traffic instead of reloading B for every M tile.

## Isolated Cases

- `smoke_1x1x1`
  Smallest non-zero case. Confirms the basic start-to-finish flow.
- `zero_m`
  `M=0`. Verifies fast exit and no modification of C.
- `zero_k`
  `K=0`. Verifies fast exit and no modification of C.
- `zero_n`
  `N=0`. Verifies fast exit and no modification of C.
- `exact_tile_random`
  `8x8x8`. Standard full-tile functional case.
- `max_values`
  All `127`. Verifies positive extreme accumulation.
- `min_values`
  All `-128`. Verifies sign extension and negative extreme accumulation.
- `odd_sizes_ramp`
  `3x11x17`. Verifies packed loads and partial-edge tiles.
- `mixed_tiling_random`
  `10x7x9`. Covers partial tiling in multiple dimensions.
- `large_multi_tile_random`
  `16x7x19`. Covers a deeper multi-tile schedule.
- `wide_k_partial_random`
  `9x13x5`. Covers multiple K tiles.

## Repeat Cases

- `repeat_same_output_base_first`
  First run writes to a fixed output base using all-ones data.
- `repeat_same_output_base_second`
  Second run writes to the same output base using random data.

These cases verify that:

- Status and completion behavior reset correctly between runs.
- The second run does not inherit stale output data from the first run.

## WS Reuse Cases

- `ws_b_reuse_single_kn_tile`
  `M=32, K=8, N=8`. Verifies B reuse across multiple M tiles for one `(K,N)` region.
- `ws_b_reuse_multi_k_tile`
  `M=16, K=16, N=8`. Verifies reuse behavior when K spans multiple tiles.
- `ws_b_reuse_multi_n_tile`
  `M=16, K=8, N=16`. Verifies reuse behavior when N spans multiple tiles.

These cases also check memory traffic statistics:

- B reads must match the expected WS reuse count, not the naive no-reuse count.
- A reads must match the number of N tiles.
- C reads must be zero.
- C writes must equal `M*N`.

## Main Checks

- Every normal case must produce a C matrix that matches the golden GEMM result.
- Guard words after the valid C region must remain unchanged.
- Zero-dimension cases must not modify `baseC`.
- After completion, the status register must report `busy=0, done=1`.
- The AXI memory model injects random stalls to verify correctness under backpressure.
