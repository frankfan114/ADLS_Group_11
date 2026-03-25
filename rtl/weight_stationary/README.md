# Weight-Stationary Design

This folder contains the baseline weight-stationary systolic array used as a reference point for the other variants in this branch.

- `rtl/`: core RTL for the baseline WS dataflow
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: MIG `example_top` bring-up files

In this design, weights stay resident in the array while activations stream through the PEs and outputs are written back after each tile.
