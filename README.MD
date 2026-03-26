# ADLS Group 11: Design Space Exploration and Layer-Aware Mapping for Systolic Array Variants

📄 **[Full Project Report](ADLS_group_11.pdf)**

## Table of Contents

- [Project Overview](#project-overview)
- [Key Contributions](#key-contributions)
- [Key Findings](#key-findings)
- [Repository Structure](#repository-structure)
- [Running the Tools](#running-the-tools)
  - [Selector](#selector)
  - [CocoTB Functional Verification](#cocotb-functional-verification)
  - [Vivado Simulation](#vivado-simulation)
- [Branches](#branches)

---

## Project Overview

This project explores how different **systolic-array architectures** impact the performance of **quantized neural network (NN) inference**, and introduces an automated toolflow for **layer-aware hardware mapping**.

We design and evaluate multiple systolic-array variants—including **Output-Stationary (OS)**, **Weight-Stationary (WS)**, **buffered (ping-pong)**, and a **flexible reconfigurable WS-based architecture**—under a unified benchmarking framework. Each variant represents a different optimization strategy (e.g., data reuse, memory overlap, or adaptability), enabling systematic analysis of trade-offs in:

- Latency and throughput
- Processing element (PE) utilization
- Stall behavior (memory bottlenecks)
- Hardware cost (LUTs, FFs, etc.)

---

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

---

## Key Findings

- **Weight-Stationary (WS)** consistently outperforms OS for reuse-heavy workloads due to reduced weight movement
- **Buffering** provides limited benefit unless communication–computation overlap is significant
- **Reconfigurability** improves utilization but does not eliminate memory bottlenecks
- Overall performance is often **memory-bound**, not compute-bound

**Takeaway:** Hardware performance for NN inference is highly sensitive to dataflow and memory behavior. A multi-architecture design space combined with benchmark-driven selection is more effective than relying on a single fixed accelerator.

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

## Running the Tools

### Selector

The selector ranks systolic array variants for a given layer shape and optionally generates patched RTL. See [`selector/README.md`](selector/README.md) for full documentation.

```bash
cd selector/systolic_selector

# BERT-tiny layer
python main.py --M 32 --K 128 --N 2

# MNIST MLP layer
python main.py --M 16 --K 16 --N 10

# Custom layer — latency-first priority, top-5 results
python main.py --M 64 --K 192 --N 10 --perf_w 0.8 --resource_w 0.2 --top_k 5
```

Reports and generated RTL are written to `selector/reports/`:

| Output                 | Path                                              |
| ---------------------- | ------------------------------------------------- |
| Markdown report        | `reports/report_M{M}_K{K}_N{N}.md`                |
| Plain-text report      | `reports/report_M{M}_K{K}_N{N}.txt`               |
| Trade-off scatter plot | `reports/plot_M{M}_K{K}_N{N}.png`                 |
| Generated RTL          | `reports/generated_rtl/rank{i}_{VARIANT}_dim{D}/` |

---

### CocoTB Functional Verification

Requires [cocotb](https://github.com/cocotb/cocotb) and [Icarus Verilog](http://iverilog.icarus.com/).

```bash
cd cocotb_verification/<design>/
PYTHONHOME=<path-to-python> make
```

> **Windows note:** `vvp` (Icarus Verilog's runtime) cannot locate the Python standard library unless `PYTHONHOME` is set explicitly. Find your path with `python -c "import sys; print(sys.prefix)"`.

Available designs: `output_stationary`, `weight_stationary`, `os_pp`, `ws_pp`, `rsa_ws`, `smt_sa`

Example:

```bash
cd cocotb_verification/weight_stationary/
PYTHONHOME="C:/Users/<username>/AppData/Local/Programs/Python/Python311" make
```

---

### Vivado Simulation

Each subdirectory under `vivado_simulation/` is a self-contained source set (`example_top.v`, `sim_tb_top.v`, hex init files).

1. Open Vivado and create or open a project.
2. Add sources from the target subdirectory, e.g. `vivado_simulation/bert_layer/`.
3. Set `sim_tb_top.v` as the simulation top module.
4. Run **Simulation → Run Behavioral Simulation**.

Available targets:

| Directory           | Description                            |
| ------------------- | -------------------------------------- |
| `bert_layer`        | BERT encoder layer benchmark           |
| `deit_layer`        | DeiT (ViT) layer benchmark             |
| `mnist_layer`       | MNIST MLP layer benchmark              |
| `output_stationary` | Output-stationary systolic array       |
| `weight_stationary` | Weight-stationary systolic array       |
| `os_pp`             | Output-stationary with post-processing |
| `ws_pp`             | Weight-stationary with post-processing |
| `rsa_ws`            | Row-skipping adaptive array            |

---

## Branches

| Branch            | Purpose                                                                              |
| ----------------- | ------------------------------------------------------------------------------------ |
| `main`            | Consolidated final state — RTL, verification, simulation, quantization, and selector |
| `variant`         | Exploration of systolic array variants experiments                                   |
| `pingpong`        | Ping-pong buffering extension for WS and OS designs                                  |
| `layer_info`      | Per-layer analysis results and selected layer weight bundles                         |
| `result+selector` | Benchmark results, resource utilization data, and selector integration               |
