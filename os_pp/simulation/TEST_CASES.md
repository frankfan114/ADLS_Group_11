# OS-PP Simulation Test Cases

This directory currently contains one cocotb regression:

- `matrix_axi_wrapper_tb.py`
  Verifies `matrix_top_wrapper`, including CPU bus programming, AXI master memory traffic, status register behavior, and final GEMM correctness.

By default, `os_pp/rtl/matrix_top_wrapper.v` builds the validated safe path and only enables the experimental PP tiled path when `USE_PP_TILED` is defined.

The wrapper regression checks register readback, status bits, and behavior under AXI backpressure.

## Case List

### Basic and Boundary Cases

- `smoke_1x1x1`
  Smallest non-zero matrix. Confirms the basic datapath, start/done flow, and signed multiply-accumulate behavior.
- `zero_m`
  `M=0`. Verifies fast exit for zero-height output and confirms that C is not modified.
- `zero_k`
  `K=0`. Verifies fast exit for zero reduction depth and confirms that C is not modified.
- `zero_n`
  `N=0`. Verifies fast exit for zero-width output and confirms that C is not modified.

### Normal Functionality and Tiling

- `exact_tile_random`
  `8x8x8`. Exact tile-sized case that exercises the standard full-array path.
- `mixed_tiling_random`
  `10x7x9`. Exercises non-exact tiling in M, K, and N simultaneously.
- `large_multi_tile_random`
  `16x7x19`. Covers multiple M tiles and multiple N tiles in one run.
- `wide_k_partial_random`
  `9x13x5`. Covers multiple K tiles and a partial last K tile.
- `odd_sizes_ramp`
  `3x11x17` with deterministic ramp data. Useful for debugging alignment and packing issues.

### Numeric Stress Cases

- `max_values`
  All inputs are `127`. Verifies positive extreme accumulation.
- `min_values`
  All inputs are `-128`. Verifies negative extreme accumulation and sign handling.

### Repeated Runs and Output Overwrite

- `repeat_same_output_base_first`
  First run writes to a fixed output base using all-ones data.
- `repeat_same_output_base_second`
  Second run writes to the same output base using random data.

These two cases verify that:

- The design can run again after completion.
- Old output data does not leak into the next run.

## Main Checks

- Every output element in C must match the golden signed GEMM result.
- Bus-programmed registers `0x00` through `0x14` must read back correctly.
- Status register `0x20` must show idle after reset and `busy=0, done=1` after completion.
- Guard words after the valid C region must remain unchanged.
- In zero-dimension cases, `baseC` itself must remain unchanged.
- The AXI memory model injects random `AW`, `W`, and `AR` stalls to verify behavior under backpressure.
