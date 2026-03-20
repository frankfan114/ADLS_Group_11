import json
import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer

from systolic_bench_common import (
    CLOCK_PERIOD_NS,
    DeterministicAxiMemoryModel,
    reset_dut,
    run_benchmark_case,
)


def load_cases():
    raw = os.environ.get("BENCHMARK_CASES_JSON")
    if not raw:
        raise RuntimeError("BENCHMARK_CASES_JSON is not set")
    return json.loads(raw)


def write_results(path_str, payload):
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@cocotb.test()
async def benchmark_matrix_top_wrapper(dut):
    cases = load_cases()
    variant = os.environ.get("BENCHMARK_VARIANT", "unknown")
    result_path = os.environ.get("BENCHMARK_RESULTS_JSON")
    if not result_path:
        raise RuntimeError("BENCHMARK_RESULTS_JSON is not set")

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD_NS, "ns").start())
    await Timer(50, "ns")

    mem = DeterministicAxiMemoryModel(dut)
    cocotb.start_soon(mem.run())

    results = []
    for case in cases:
        await reset_dut(dut)
        result = await run_benchmark_case(dut, mem, case)
        result["variant"] = variant
        results.append(result)

    payload = {
        "variant": variant,
        "clock_period_ns": CLOCK_PERIOD_NS,
        "results": results,
    }
    write_results(result_path, payload)
    dut._log.info(f"Wrote benchmark results to {result_path}")
