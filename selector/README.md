# Selector

Automated systolic array variant selector and RTL generator. Given a matrix multiplication shape `(M, K, N)`, the tool ranks all benchmarked hardware configurations by a weighted performance–resource score, optionally generates patched RTL for the top picks, and saves a full report.

## Directory Structure

```
selector/
├── systolic_selector/       # Python tool
│   ├── main.py              # CLI entry point
│   ├── loader.py            # CSV ingestion and normalisation
│   ├── selector.py          # Nearest-neighbour scoring engine
│   ├── report.py            # Text / Markdown report and scatter plot
│   ├── generator.py         # RTL patch generator
│   └── requirements.txt     # Python dependencies
├── benchmark_csv/           # Reference benchmark data (one CSV per run)
├── reports/                 # Auto-generated reports, plots, and RTL
│   └── generated_rtl/       # Patched RTL folders (rank1_*, rank2_*, ...)
└── resouces/                # Resource utilisation reference data
```

## Installation

```bash
pip install -r selector/systolic_selector/requirements.txt
```

Dependencies: `numpy>=1.24`, `matplotlib>=3.7` (optional, needed for plots only).

## Usage

Run from the `selector/systolic_selector/` directory:

```bash
cd selector/systolic_selector

# BERT-tiny encoder layer
python main.py --M 32 --K 128 --N 2

# MNIST MLP layer
python main.py --M 16 --K 16 --N 10

# Custom layer — latency-first, top-5 results
python main.py --M 64 --K 192 --N 10 --perf_w 0.8 --resource_w 0.2 --top_k 5

# Suppress plot window
python main.py --M 32 --K 128 --N 2 --no_plot

# Skip RTL generation
python main.py --M 64 --K 192 --N 10 --no_generate
```

### All flags

| Flag | Default | Description |
|------|---------|-------------|
| `--M` | *(required)* | Output rows / batch size |
| `--K` | *(required)* | Reduction dimension / input features |
| `--N` | *(required)* | Output columns / neurons |
| `--perf_w` | 0.6 | Weight on performance score (0–1) |
| `--resource_w` | 0.4 | Weight on resource score (0–1) |
| `--top_k` | 2 | Number of top configurations to return |
| `--csv_dir` | `../benchmark_csv` | Path to benchmark CSV folder |
| `--out_dir` | `../reports` | Output directory for reports and RTL |
| `--rtl_dir` | `../../rtl` | Root RTL source directory |
| `--no_plot` | — | Disable trade-off scatter plot |
| `--no_generate` | — | Disable RTL generation |

## Outputs

All outputs are written to `selector/reports/`:

| File | Description |
|------|-------------|
| `report_M{M}_K{K}_N{N}.md` | Full markdown report with ranked table |
| `report_M{M}_K{K}_N{N}.txt` | Plain-text version (also printed to terminal) |
| `plot_M{M}_K{K}_N{N}.png` | Performance vs. resource scatter plot |
| `generated_rtl/rank{i}_{VARIANT}_dim{D}/` | Patched RTL folder for each top-k pick |

## Scoring Model

The composite score is:

```
score = w_perf × perf_score + w_resource × resource_score
```

**Performance sub-weights** (fixed):

| Metric | Weight |
|--------|--------|
| `latency_cycles` | 0.50 |
| `throughput_mac_per_cycle` | 0.30 |
| `memory_stall_ratio` | 0.20 |

**Resource sub-weights** (fixed):

| Metric | Weight |
|--------|--------|
| `physical_pe_count` | 0.40 |
| `read_bytes` | 0.30 |
| `b_reads` | 0.20 |
| `pe_utilization` | 0.10 |

The nearest reference point is found using a weighted Euclidean distance over `(M, K, N)` with `K:M:N = 0.5:0.3:0.2`, reflecting that the reduction dimension has the strongest impact on memory access patterns.
