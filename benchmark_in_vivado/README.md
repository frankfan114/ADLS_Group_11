# Vivado Benchmark TB

`benchmark_sim_tb_top.v` is a Vivado/XSim-friendly matrix benchmark testbench for `example_top` designs that look like [`ws_tb/example_top.v`](../ws_tb/example_top.v): the top owns the MIG7 DDR interface, and the matrix wrapper reaches DDR through AXI.

## What it does

- Waits for MIG calibration to finish.
- Forces `u_ip_top.matrix_cfg_state` idle so the TB can drive the wrapper config bus.
- Preloads A/B through the MIG AXI slave interface.
- Starts the matrix wrapper through `matrix_bus_*`.
- Waits for `u_ip_top.u_matrix_top_wrapper.sys_done`.
- Reads C back through AXI and checks against a software-generated golden result.
- Prints per-case benchmark lines with `BENCH_RESULT,...` so logs are easy to grep or post-process.
- Writes a structured `benchmark_results.csv` next to the TB run directory.

## Default benchmark sweep

The quick-edit section is near the top of [`benchmark_sim_tb_top.v`](./benchmark_sim_tb_top.v). By default it runs 6 cases:

- `8x8 x 8x8`
- `32x8 x 8x8`
- `16x16 x 16x8`
- `16x8 x 8x16`
- `32x16 x 16x8`
- `24x12 x 12x12`

## Run with XSim

From the repo root:

```powershell
cd benchmark_in_vivado
xvlog -f ws_benchmark_xsim_files.prj
xelab work.benchmark_sim_tb_top work.glbl -s ws_vivado_benchmark
xsim ws_vivado_benchmark -runall
```

After the run finishes, collect a JSON summary with:

```powershell
python collect_results.py
```

If you only kept the XSim console log, you can also parse that directly:

```powershell
python collect_results.py --input xsim.log --csv-out benchmark_results_from_log.csv
```

## Notes

- The file list in [`ws_benchmark_xsim_files.prj`](./ws_benchmark_xsim_files.prj) is wired to the WS `example_top` and WS matrix RTL.
- If you later want to benchmark another `example_top` variant with the same MIG7 + AXI shape, keep this TB and swap the relevant source entries in the `.prj`.
- The main machine-readable outputs are `benchmark_results.csv` and the JSON emitted by [`collect_results.py`](./collect_results.py).
