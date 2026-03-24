# SMT Systolic Array Design

This folder contains the systolic-array variant with per-PE SMT-style threading.

- `rtl/`: SMT-aware RTL, including the `SMT_THREADS` parameter carried through `matrix_top_wrapper.v`, `matrix_tiled.sv`, `matrix_systolic_array.sv`, and `matrix_pe.sv`
- `simulation/`: cocotb / Icarus regression collateral

Compared with the baseline array, each PE can track multiple in-flight work items, which makes this directory the branch's multithreaded systolic-array experiment.
