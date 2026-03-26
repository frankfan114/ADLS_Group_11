# systolic_selector

Python implementation of the automated systolic array selector. This package loads benchmark data, scores all candidate configurations against a query layer shape, and optionally generates patched RTL for the top picks.

## Modules

| File | Role |
|------|------|
| `main.py` | CLI entry point — parses arguments and orchestrates the pipeline |
| `loader.py` | Ingests benchmark CSVs and attaches variant/dim metadata |
| `selector.py` | Nearest-neighbour scoring engine |
| `report.py` | Generates text/Markdown reports and a scatter plot |
| `generator.py` | Copies and patches RTL source for each top-K result |
| `requirements.txt` | Python dependencies |

## Pipeline

```
benchmark_csv/          loader.py            selector.py
  *.csv  ──────────►  load_reference_data  ──►  select_top_k
                                                     │
                              ┌──────────────────────┤
                              ▼                      ▼
                          report.py            generator.py
                     (text + markdown     (copy RTL + patch
                      + scatter plot)      MAX_M/K/N params)
```

1. **loader** — reads all 22 benchmark CSVs from `../benchmark_csv/`. Each file is mapped to a `(variant, dim, layer)` triple via a hard-coded table (filenames are inconsistent so parsing is not reliable). Returns a flat list of records with all numeric columns plus metadata.

2. **selector** — for each `(variant, dim)` configuration, finds the nearest reference record by weighted Euclidean distance over `(M, K, N)` with weights `K:M:N = 0.5:0.3:0.2`. Interpolated metrics are then scored:

   ```
   score = w_perf × perf_score + w_resource × resource_score
   ```

   Internal sub-weights are fixed (see [`../README.md`](../README.md#scoring-model)).

3. **report** — emits a ranked table to stdout and saves `.txt` / `.md` files to `../reports/`. Also computes the Pareto front (minimising `latency_cycles` vs `read_bytes`) and renders a scatter plot.

4. **generator** — for each top-K result, copies the matching RTL subfolder from `../../rtl/<variant>/` into `../reports/generated_rtl/rank{i}_{VARIANT}_dim{D}/`, patches `MAX_M`, `MAX_K`, `MAX_N` in `matrix_top_wrapper.v` to the selected `dim`, and writes a `selector_config.txt` manifest.

## Usage

```bash
cd selector/systolic_selector

python main.py --M <M> --K <K> --N <N> [options]
```

See [`../README.md`](../README.md) for the full flag reference and output description.

## Reference Layers

The benchmark data covers two reference layers:

| Layer | M | K | N |
|-------|---|---|---|
| BERT-tiny (linear) | 32 | 128 | 2 |
| MNIST MLP (linear) | 16 | 16 | 10 |

Queries outside these shapes are handled by interpolation from the nearest reference point.
