TOPLEVEL ?= matrix_top_wrapper
MODULE ?= matrix_axi_wrapper_tb
SIM ?= icarus
SIM_BUILD ?= sim_build_$(TOPLEVEL)
RESULTS_XML ?= matrix_wrapper_results.xml
PYTHON ?= python

.PHONY: all sim clean

all: sim

sim:
	$(PYTHON) run_cocotb.py

clean:
	-$(PYTHON) -c "from pathlib import Path; import shutil; shutil.rmtree(Path('$(SIM_BUILD)'), ignore_errors=True); Path('$(RESULTS_XML)').unlink(missing_ok=True)"
