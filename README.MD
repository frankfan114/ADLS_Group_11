# ADL Variant Branch

This branch is mainly a collection of systolic-array design variants and their verification collateral.

## Design Folders

- `weight_stationary/`: baseline weight-stationary design
- `output_stationary/`: baseline output-stationary design
- `ws_pp/`: weight-stationary design with ping-pong writeback
- `os_pp/`: output-stationary design with ping-pong writeback
- `rsa_ws/`: adaptive weight-stationary design with runtime array selection and masking
- `smt_sa/`: SMT-style multithreaded systolic-array experiment

Most design folders use the same top-level structure:

- `rtl/`: synthesizable RTL
- `simulation/`: cocotb / Icarus regression collateral
- `vivado/`: Vivado `example_top` bring-up collateral

Each design folder now has its own short `README.md` with the local design summary. `rsa_ws/README.md` also includes a more detailed regression example for the adaptive WS variant.

## How To Read This Branch

- Start from the design folder that matches the dataflow you want to inspect.
- Read its local `README.md` first, then go into `rtl/` for the implementation.
- Use `simulation/` for regression collateral and `vivado/` when you need the MIG `example_top` flow.

## Layer Cases

There are also two layer-specific bring-up cases:

- `bert_layer/`: baked BERT Tiny workload on top of the MIG `example_top` flow
- `mnist_layer/`: baked MNIST MLP workload on top of the same flow

These are supporting case-study folders rather than the main organization of the branch.

## Reports

- `resource.md`: consolidated Vivado utilization reports for checked-in `example_top` builds

## Quick Start

- For architecture comparison, work from the six design folders listed above.
- For implementation details, open the local folder `README.md` and then inspect `rtl/`.
- Use `bert_layer/` and `mnist_layer/` only when you want workload-specific bring-up cases.
