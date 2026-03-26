TOPLEVEL_LANG = verilog
SIM ?= icarus
COMPILE_ARGS += -g2012

# Default target for current matrix AXI-wrapper simulation
TOPLEVEL ?= matrix_top_wrapper
MODULE   ?= matrix_axi_wrapper_tb

# Compile only matrix-related RTL for faster and cleaner sims.
RTL_DIR := $(CURDIR)/../../rtl/smt_sa
VERILOG_SOURCES := $(shell find $(RTL_DIR) -type f \( -name "*.v" -o -name "*.sv" \) | sort)
include $(shell cocotb-config --makefiles)/Makefile.sim
