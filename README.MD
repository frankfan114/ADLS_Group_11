# ADL Group 11

Systolic array accelerator design project covering RTL implementation, verification, simulation, quantization analysis, and automated design selection.

## Repository Structure

| Folder | Contents |
|--------|----------|
| [`rtl/`](rtl/) | SystemVerilog/Verilog RTL source for six systolic array designs (`output_stationary`, `weight_stationary`, `os_pp`, `ws_pp`, `rsa_ws`, `smt_sa`). Each design shares the `matrix_top_wrapper` top-level interface. |
| [`cocotb_verification/`](cocotb_verification/) | Python-based cocotb functional verification testbenches for each RTL design. Each subdirectory contains a testbench (`matrix_axi_wrapper_tb.py`), a `Makefile`, and a `TEST_CASES.md`. |
| [`vivado_simulation/`](vivado_simulation/) | Vivado-compatible simulation files for the systolic array designs and neural network layer demos (BERT, DeiT, MNIST). Each subdirectory has a top-level wrapper, a testbench, and hex weight/data init files. |
| [`quantization_analysis/`](quantization_analysis/) | PyTorch PTQ/QAT sweep, per-layer profiling, and weight export scripts. Covers ResNet18/50 and BERT-tiny; outputs sweep metrics, checkpoints, and per-layer JSON profiles. |
| [`selector/`](selector/) | Automated systolic array selector and RTL generator. Given a workload shape, `systolic_selector/` ranks designs using benchmark CSVs, generates RTL, and produces comparison reports. |
