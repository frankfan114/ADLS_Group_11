# Output-Stationary Design

This folder contains the baseline output-stationary systolic array.

- `rtl/`: core RTL for the OS dataflow, including the top/down and left/right wavefront feeders
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: MIG `example_top` bring-up files

In this design, partial sums stay inside the array during computation, while activations and weights are injected through wavefront-style preload paths.
