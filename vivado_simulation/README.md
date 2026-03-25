# Vivado Simulation

Vivado-compatible simulation files for both the systolic array designs and neural network layer demos. Each subdirectory contains:

| File | Description |
|------|-------------|
| `example_top.v` | Top-level wrapper instantiation for Vivado |
| `sim_tb_top.v`  | Simulation testbench |
| `*.vh`          | Hex weight/data initialization files (where applicable) |

## Subdirectories

| Directory | Type |
|-----------|------|
| `bert_layer`        | BERT encoder layer demo |
| `deit_layer`        | DeiT (ViT) layer demo |
| `mnist_layer`       | MNIST MLP layer demo |
| `output_stationary` | Output-stationary systolic array |
| `weight_stationary` | Weight-stationary systolic array |
| `os_pp`             | Output-stationary with post-processing |
| `ws_pp`             | Weight-stationary with post-processing |
| `rsa_ws`            | Row-skipping adaptive array |
