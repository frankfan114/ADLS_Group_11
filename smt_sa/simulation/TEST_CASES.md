# SMT-SA Simulation Test Cases

The cocotb regression in this directory is `matrix_axi_wrapper_tb.py`, which verifies `matrix_top_wrapper`.

The regression structure is very similar to `weight_stationary`, but it targets the SMT-SA implementation. It therefore checks both functional correctness and system-level B reuse behavior.

## Isolated Cases

- `smoke_1x1x1`
  Smallest non-zero case. Confirms the basic datapath.
- `zero_m`
  `M=0`. Verifies fast exit and no modification of C.
- `zero_k`
  `K=0`. Verifies fast exit and no modification of C.
- `zero_n`
  `N=0`. Verifies fast exit and no modification of C.
- `exact_tile_random`
  `8x8x8`. Standard exact-tile functional case.
- `max_values`
  All `127`. Verifies positive extreme accumulation.
- `min_values`
  All `-128`. Verifies negative extreme accumulation.
- `odd_sizes_ramp`
  `3x11x17`. Verifies packed loads and edge tiles.
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

These cases verify that the output region is fully refreshed and that the state machine resets correctly for the next run.

## WS-Style Reuse Cases

- `ws_b_reuse_single_kn_tile`
  `M=32, K=8, N=8`. Verifies B reuse across multiple M tiles for a fixed `(K,N)` region.
- `ws_b_reuse_multi_k_tile`
  `M=16, K=16, N=8`. Verifies B traffic when K spans multiple tiles.
- `ws_b_reuse_multi_n_tile`
  `M=16, K=8, N=16`. Verifies B traffic when N spans multiple tiles.

These cases also track memory traffic:

- B reads must match the expected reuse count.
- A reads must match the tile schedule.
- C reads must be zero.
- C writes must equal `M*N`.

## Main Checks

- Every normal case must produce a C matrix that matches the golden GEMM result.
- Zero-dimension cases must not modify the output region.
- Guard words after the valid C region must remain unchanged.
- After completion, the status register must report `busy=0, done=1`.
- The AXI memory model injects random stalls to verify correctness under backpressure.
