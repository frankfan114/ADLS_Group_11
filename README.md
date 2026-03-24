# ADL Group 11 - Benchmark Results

This branch (`result`) contains benchmark CSV files collected from hardware accelerator simulations.

## Contents

All files are located in [`benchmark_csv/`](benchmark_csv/) (23 files total).

### Models

| Model | Description |
|-------|-------------|
| `minst` / `mnist_mlp` | MNIST MLP (16×16×10) |
| `bert` / `bert_tiny` | BERT-Tiny (32×128×2) |
| `deit` | DeiT (64×192×10) |

### Dataflow Configurations

| Prefix | Dataflow |
|--------|----------|
| `os` | Output Stationary |
| `ws` | Weight Stationary |
| `rsa` | Row Stationary A |
| `pp` | Pipeline Parallel |

### Naming Convention

```
<dataflow>+<model>+<parallelism>.csv
```

e.g., `os+bert+16.csv` = Output Stationary, BERT-Tiny, parallelism 16.

## CSV Columns

Each CSV includes per-layer simulation metrics:

- **Timing**: `preload_ps`, `cfg_ps`, `run_ps`, `readback_ps`, `latency_cycles`
- **Compute**: `useful_macs`, `pe_utilization`, `throughput_mac_per_cycle`
- **Memory**: `memory_stall_cycles`, `memory_stall_ratio`, `dma_busy_ratio`
- **AXI Bus**: `ar_requests`, `aw_requests`, `read_beats`, `write_beats`
- **Accuracy**: `mismatch_count`, `max_abs_error`, `mean_abs_error`
