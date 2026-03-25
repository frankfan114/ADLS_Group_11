# CocoTB Verification

Python-based functional verification testbenches using [cocotb](https://github.com/cocotb/cocotb). Each subdirectory corresponds to an RTL design in `../rtl/` and contains:

| File | Description |
|------|-------------|
| `matrix_axi_wrapper_tb.py` | Main testbench driving the AXI bus interface |
| `Makefile` | Build/run entry point (`make SIM=verilator`) |
| `TEST_CASES.md` | Description of covered test cases |

## Designs

`os_pp` · `output_stationary` · `rsa_ws` · `smt_sa` · `weight_stationary` · `ws_pp`

## Quick Start

```bash
cd <design>/
make SIM=verilator
```
