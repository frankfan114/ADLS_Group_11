# ADLS Group 11 -- Design Space Exploration and Layer-Aware Mapping for Systolic Array Variants

## Project Overview

This project explores how different **systolic-array architectures** impact the performance of **quantized neural network (NN) inference**, and introduces an automated toolflow for **layer-aware hardware mapping**.

We design and evaluate multiple systolic-array variants—including **Output-Stationary (OS)**, **Weight-Stationary (WS)**, **buffered (ping-pong)**, and a **flexible reconfigurable WS-based architecture**—under a unified benchmarking framework. Each variant represents a different optimization strategy (e.g., data reuse, memory overlap, or adaptability), enabling systematic analysis of trade-offs in:

- Latency and throughput
- Processing element (PE) utilization
- Stall behavior (memory bottlenecks)
- Hardware cost (LUTs, FFs, etc.)

## Key Contributions

### 1. Hardware Design Space Exploration

- Implemented multiple systolic-array dataflows with consistent interfaces and evaluation methodology
- Compared architectural trade-offs across compute efficiency, memory behavior, and resource usage
- Demonstrated that **no single architecture is optimal** across all NN layer shapes

### 2. Buffered and Flexible Extensions

- Added **ping-pong buffering** to overlap computation and memory access (beneficial only under sufficient overlap)
- Developed a **reconfigurable WS-based design** to improve utilization under mismatched layer shapes

### 3. Benchmark-Driven Evaluation Framework

- Built a unified FPGA-based benchmarking flow (DDR-backed memory model)
- Collected metrics including latency, throughput, utilization, stalls, and resource usage
- Enabled reproducible and fair comparison across architectures

### 4. Automated Layer-to-Hardware Mapping Tool

- Introduced a lightweight toolflow that:
  - Profiles hardware variants offline
  - Predicts performance for new layers via interpolation
  - Ranks candidate configurations using a weighted scoring function
  - Generates the corresponding RTL configuration
- Avoids exhaustive search while still achieving effective design selection

## Key Findings

- **Weight-Stationary (WS)** consistently outperforms OS for reuse-heavy workloads due to reduced weight movement
- **Buffering** provides limited benefit unless communication–computation overlap is significant
- **Reconfigurability** improves utilization but does not eliminate memory bottlenecks
- Overall performance is often **memory-bound**, not compute-bound

## Takeaway

Hardware performance for NN inference is highly sensitive to **dataflow and memory behavior**. A **multi-architecture design space** combined with **benchmark-driven selection** is more effective than relying on a single fixed accelerator, and lightweight automated mapping can bridge the gap between **hardware specialization** and **workload diversity**.

---

## Repository Structure

| Folder                                             | Contents                                                                                                                                                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`rtl/`](rtl/)                                     | SystemVerilog/Verilog RTL source for six systolic array designs (`output_stationary`, `weight_stationary`, `os_pp`, `ws_pp`, `rsa_ws`, `smt_sa`). Each design shares the `matrix_top_wrapper` top-level interface. |
| [`cocotb_verification/`](cocotb_verification/)     | Python-based cocotb functional verification testbenches for each RTL design. Each subdirectory contains a testbench (`matrix_axi_wrapper_tb.py`), a `Makefile`, and a `TEST_CASES.md`.                             |
| [`vivado_simulation/`](vivado_simulation/)         | Vivado-compatible simulation files for the systolic array designs and neural network layer demos (BERT, DeiT, MNIST). Each subdirectory has a top-level wrapper, a testbench, and hex weight/data init files.      |
| [`quantization_analysis/`](quantization_analysis/) | PyTorch PTQ/QAT sweep, per-layer profiling, and weight export scripts. Covers ResNet18/50 and BERT-tiny; outputs sweep metrics, checkpoints, and per-layer JSON profiles.                                          |
| [`selector/`](selector/)                           | Automated systolic array selector and RTL generator. Given a workload shape, `systolic_selector/` ranks designs using benchmark CSVs, generates RTL, and produces comparison reports.                              |

---

## Branches

Development was split across several branches, each focused on a specific aspect of the project:

| Branch                       | Purpose                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| `main`                       | Consolidated final state — RTL, verification, simulation, quantization, and selector |
| `variant`                    | Exploration of systolic array variants experiments                                   |
| `pingpong`                   | Ping-pong buffering extension for WS and OS designs                                  |
| `layer_info`                 | Per-layer analysis results and selected layer weight bundles                         |
| `result` / `result+selector` | Benchmark results, resource utilization data, and selector integration               |
