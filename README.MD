# ADL Variant Branch

This branch is organized around two kinds of content:

- reusable design variants under their own implementation folders
- layer-specific bring-up cases that reuse the MIG `example_top` flow

## Design Variants

- `weight_stationary/`: baseline weight-stationary array
- `output_stationary/`: baseline output-stationary array
- `os_pp/`: output-stationary with ping-pong writeback path
- `ws_pp/`: weight-stationary with ping-pong writeback path
- `rsa_ws/`: adaptive weight-stationary variant with runtime array selection
- `smt_sa/`: alternate systolic-array variant used for comparison

Each design variant keeps the same top-level structure when available:

- `rtl/`: synthesizable RTL
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: Vivado `example_top` bring-up collateral

`rsa_ws/README.md` contains the detailed regression command for the adaptive WS design.

## Layer Cases

- `bert_layer/`: baked BERT Tiny classifier case with dimensions `M=32`, `K=128`, `N=2`
- `mnist_layer/`: baked MNIST MLP classifier case with dimensions `M=16`, `K=16`, `N=10`

Both layer-case folders follow the same layout:

- `example_top.v`: single-case Vivado bring-up wrapper
- `sim_tb_top.v`: multi-case benchmark / verification testbench
- `*.vh`: baked case data consumed by `sim_tb_top.v`

Tracked benchmark snapshots are kept at the repository root:

- `bert_layer_4_4_32x128x2.csv`
- `bert_layer_8_8_32x128x2.csv`
- `mnist_layer_4_4_16x16x10.csv`
- `mnist_layer_8_8_16x16x10.csv`

If a layer testbench is run with a nonstandard array shape, it falls back to a `*_case0_*.csv` file name. Those scratch outputs are ignored in `.gitignore`.

## Reports

- `resource.md`: consolidated Vivado utilization reports for checked-in `example_top` builds

## Quick Start

- Use the design-variant folders for reusable RTL and cocotb regressions.
- Use `bert_layer/sim_tb_top.v` and `mnist_layer/sim_tb_top.v` for layer-level benchmark bring-up.
- Use the root CSV snapshots for quick resource / latency comparisons across array sizes.
