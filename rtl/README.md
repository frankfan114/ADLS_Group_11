# RTL Designs

SystemVerilog/Verilog RTL source for six systolic array accelerator designs. Each subdirectory is a self-contained design with a shared top-level interface (`matrix_top_wrapper`).

| Design | Description |
|--------|-------------|
| `output_stationary` | Output-stationary dataflow systolic array |
| `weight_stationary` | Weight-stationary dataflow systolic array |
| `os_pp`             | Output-stationary with post-processing pipeline |
| `ws_pp`             | Weight-stationary with post-processing pipeline |
| `rsa_ws`            | Row-skipping adaptive weight-stationary array |
| `smt_sa`            | Simultaneous multi-threading systolic array |

## Parameters

All designs expose the following top-level parameters in `matrix_top_wrapper`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_M`   | 8       | Maximum number of output rows |
| `MAX_K`   | 8       | Maximum inner (reduction) dimension |
| `MAX_N`   | 8       | Maximum number of output columns |
