# Weight-Stationary Ping-Pong Design

This folder contains the weight-stationary design extended with ping-pong writeback support.

- `rtl/`: WS RTL plus `matrix_writeback_pp.sv`, `matrix_tilednopp.sv`, and the split AXI bridge
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: MIG `example_top` bring-up files

Compared with `weight_stationary/`, this variant keeps the WS dataflow but overlaps compute and output draining with a ping-pong result path.
