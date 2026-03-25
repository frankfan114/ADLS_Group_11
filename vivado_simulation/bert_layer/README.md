# BERT Layer Case

This folder holds a baked BERT Tiny classifier workload on top of the DDR/MIG `example_top` flow.

- `example_top.v`: single-case bring-up wrapper for Vivado-oriented testing
- `sim_tb_top.v`: layer-level benchmark and correctness testbench
- `case0_json_data.vh`: baked BERT input / weight / golden-output data

When the testbench is launched from the repository root, benchmark snapshots are emitted as:

- `bert_layer_4_4_32x128x2.csv`
- `bert_layer_8_8_32x128x2.csv`

Nonstandard array sizes fall back to `bert_layer_case0_32x128x2.csv`, which is gitignored.
