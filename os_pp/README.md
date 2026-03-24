# Output-Stationary Ping-Pong Design

This folder contains the output-stationary design extended with ping-pong accumulation and writeback support.

- `rtl/`: OS RTL plus ping-pong writeback logic such as `matrix_writeback_pp.sv` and the split AXI bridge
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: MIG `example_top` bring-up files

Compared with `output_stationary/`, this variant adds double-buffered result handling so one bank can be drained while the next tile continues computing.
