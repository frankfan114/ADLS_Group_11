# MNIST Layer Case

This folder holds a baked MNIST MLP classifier workload on top of the DDR/MIG `example_top` flow.

- `example_top.v`: single-case bring-up wrapper for Vivado-oriented testing
- `sim_tb_top.v`: layer-level benchmark and correctness testbench
- `mnist_mlp_w8_qat_raw_json_data.vh`: baked MNIST input / weight / golden-output data

When the testbench is launched from the repository root, benchmark snapshots are emitted as:

- `mnist_layer_4_4_16x16x10.csv`
- `mnist_layer_8_8_16x16x10.csv`

Nonstandard array sizes fall back to `mnist_layer_case0_16x16x10.csv`, which is gitignored.
