# SARA-Style Adaptive Weight-Stationary Design

`sara_ws/` is a copy of the original `weight_stationary/` baseline with a SARA/ADAPTNET-inspired runtime-reconfigurable array on top.

## What Changed

- The fixed WS array is extended with row and column bypass masks.
- The tile scheduler now supports runtime-selectable array shapes instead of only the fixed `8x8` shape.
- An `ADAPTNET`-style selector chooses a candidate array configuration automatically from workload shape.
- Manual sparse masks are also supported, so logical rows and columns can be compacted onto non-contiguous physical PEs.
- Packed-B fetch now supports sub-word column offsets, which allows flexible `N`-tiling beyond word-aligned `8x8` only scheduling.

## Main RTL

- `rtl/matrix_adaptnet_selector.sv`
  ADAPTNET-style configuration selector.
- `rtl/matrix_systolic_array.sv`
  Row/column bypass-aware PE mapping.
- `rtl/matrix_fetch.sv`
  Fetch path with programmable column offset for flexible B-tile alignment.
- `rtl/matrix_tiled.sv`
  Runtime-configurable tiler and config latch.
- `rtl/matrix_top_wrapper.v`
  CPU-visible control/status registers for auto/manual array configuration.

## Extra Registers

- `0x24`: config control
  `bit[0] = 1` enables auto configuration, `0` selects manual masks.
- `0x28`: manual row mask
- `0x2C`: manual column mask
- `0x30`: selected configuration status
  `{cfg_id[31:24], active_cols[23:16], active_rows[15:8], 8'h00}`
- `0x34`: selected masks
  `{16'h0000, selected_col_mask[15:8], selected_row_mask[7:0]}`

`cfg_id = 8'h80` means manual mode. Auto mode uses candidate IDs `0..6`.

## Verification

Run the cocotb regression for the new design:

```powershell
python -c "from pathlib import Path; from cocotb_tools.runner import get_runner; rtl=Path(r'd:\Document\ADL_Group_11\rsa_ws\rtl'); sim=Path(r'd:\Document\ADL_Group_11\rsa_ws\simulation'); sources=sorted([str(p) for p in rtl.rglob('*.sv')] + [str(p) for p in rtl.rglob('*.v')]); r=get_runner('icarus'); r.build(verilog_sources=sources, hdl_toplevel='matrix_top_wrapper', build_dir=str(sim/'sim_build_matrix_wrapper'), always=True); r.test(hdl_toplevel='matrix_top_wrapper', test_module='matrix_axi_wrapper_tb', test_dir=str(sim), results_xml=str(sim/'matrix_wrapper_results.xml'))"
```

The included regression covers:

- dense auto mode
- manual sparse bypass mode
- auto-selected `4x4`, `4x8`, `8x4`, and `2x2` shapes
- B-tile reuse preservation under a smaller manual row configuration
