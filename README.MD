# ADL Group 11 — Ping-Pong Accumulation Buffer Branch

## Branch Overview

This branch (`pingpong`) implements a **ping-pong double-buffering scheme** for the accumulation stage of the tiled systolic-array matrix multiplier. The key idea is to overlap tile writeback with the next tile's computation, hiding memory-write latency and improving overall throughput.

## Directory Structure

```
pp/matrix/          RTL source — ping-pong enabled design
pp_tb/              Testbench for pp design (Xilinx DDR3 simulation)
ws_tb_pp/           Weight-stationary testbench with ping-pong
weight_stationary_pp/  Weight-stationary RTL + cocotb simulation
base_tb/            Base testbench (Xilinx MIG reference)
```

## Key RTL Modules (`pp/matrix/`)

| File | Description |
|---|---|
| `matrix_pe.sv` | Processing Element — pipelined signed MAC (INT8 × INT8 → ACC32) |
| `matrix_systolic_array.sv` | MAX_M × MAX_N systolic array of PEs |
| `matrix_core.sv` | One-tile compute core: fetch → systolic array |
| `matrix_fetch.sv` | Reads A/B tiles from memory into the systolic array |
| `matrix_tiled.sv` | **Top tiling controller with ping-pong buffers** |
| `matrix_tilednopp.sv` | Same tiling controller but without ping-pong (baseline for comparison) |
| `matrix_writeback_pp.sv` | PP-optimised writeback — optional `SKIP_ZERO_WRITES` for sparse output |
| `matrix_writeback.sv` | Standard writeback (non-PP) |
| `matrix_leftright_wavefront.sv` | Left-right wavefront preprocessor for input A |
| `matrix_topdown_wavefront.sv` | Top-down wavefront preprocessor |
| `matrix_axi_master_bridge.sv` | AXI4 master bridge connecting the core to DDR |
| `matrix_axi_master_bridge_split.sv` | Split-channel AXI bridge variant |
| `matrix_top_wrapper.v` | Top-level wrapper (AXI + tiled core) |

## Ping-Pong Mechanism

`matrix_tiled.sv` maintains two accumulation banks:

```
c_accum_ping  [ACC_W × MAX_M × MAX_N]
c_accum_pong  [ACC_W × MAX_M × MAX_N]
active_bank   — selects which bank is being accumulated into
```

**State machine:** `CS_IDLE → CS_INIT_TILE → CS_START_CORE → CS_WAIT_CORE → CS_ACCUM → CS_COMMIT`

- After the last K-tile of a (M, N) tile pair, the controller enters `CS_COMMIT` and hands the finished bank off to `matrix_writeback_pp`.
- While writeback drains the committed bank, `active_bank` flips and the next tile begins accumulating into the free bank.
- This hides writeback latency behind compute, especially for large matrices.

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `DATA_W` | 8 | Input data width (bits) |
| `ACC_W` | 32 | Accumulator width (bits) |
| `MAX_M` | 8 | Max tile rows |
| `MAX_K` | 8 | Max tile inner dimension |
| `MAX_N` | 8 | Max tile columns |
| `SRAM_W` | 32 | Memory word width |
| `PE_PIPE` | 1 | PE pipeline stages |

## Simulation

### Icarus Verilog (syntax check)

```bash
# Full wrapper
iverilog -g2012 -s matrix_top_wrapper -o matrix_top_wrapper_pp_check.vvp \
    pp/matrix/matrix_fetch.sv pp/matrix/matrix_pe.sv \
    pp/matrix/matrix_systolic_array.sv pp/matrix/matrix_core.sv \
    pp/matrix/matrix_writeback_pp.sv pp/matrix/matrix_tiled.sv \
    pp/matrix/matrix_axi_master_bridge.sv pp/matrix/matrix_top_wrapper.v

# Tiled core only
iverilog -g2012 -s matrix_tiled -o matrix_tiled_pp_check.vvp \
    pp/matrix/matrix_fetch.sv pp/matrix/matrix_pe.sv \
    pp/matrix/matrix_systolic_array.sv pp/matrix/matrix_core.sv \
    pp/matrix/matrix_writeback_pp.sv pp/matrix/matrix_tiled.sv
```

### cocotb (weight_stationary_pp)

```bash
cd weight_stationary_pp/simulation
make
```

### Vivado / ModelSim (DDR3 testbench)

See `pp_tb/xsim_run.bat` (Windows) or `pp_tb/ies_run.sh` / `pp_tb/vcs_run.sh` (Linux).
