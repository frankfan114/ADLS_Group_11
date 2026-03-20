import csv
import json
from pathlib import Path

from cocotb_tools.runner import get_runner


ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "benchmark"
RESULTS_DIR = BENCH_DIR / "results"
TOPLEVEL = "matrix_top_wrapper"
TEST_MODULE = "systolic_axi_benchmark_tb"


VARIANTS = {
    "os": ROOT / "output_stationary" / "matrix",
    "ws": ROOT / "weight_stationary" / "matrix",
}


WORKLOADS = [
    {"workload": "tile_square", "M": 8, "K": 8, "N": 8},
    {"workload": "m_reuse", "M": 32, "K": 8, "N": 8},
    {"workload": "k_tiled", "M": 16, "K": 16, "N": 8},
    {"workload": "n_tiled", "M": 16, "K": 8, "N": 16},
]


MEMORY_PROFILES = [
    {
        "profile": "ideal",
        "memory": {
            "wait_prob": 0.0,
            "max_wait": 1,
        },
    },
    {
        "profile": "moderate",
        "memory": {
            "wait_prob": 0.10,
            "max_wait": 3,
        },
    },
    {
        "profile": "constrained",
        "memory": {
            "wait_prob": 0.20,
            "max_wait": 4,
        },
    },
]


def variant_sources(rtl_dir: Path):
    return sorted([str(p) for p in rtl_dir.rglob("*.sv")] + [str(p) for p in rtl_dir.rglob("*.v")])


def build_cases():
    cases = []
    seed = 2026
    for workload in WORKLOADS:
        for profile in MEMORY_PROFILES:
            case = {
                "case_name": f"{workload['workload']}__{profile['profile']}",
                "workload": workload["workload"],
                "profile": profile["profile"],
                "M": workload["M"],
                "K": workload["K"],
                "N": workload["N"],
                "data_mode": "random",
                "seed": seed,
                "memory": profile["memory"],
            }
            cases.append(case)
            seed += 1
    return cases


def run_variant(variant: str, rtl_dir: Path, cases):
    variant_result_json = RESULTS_DIR / f"{variant}_results.json"
    variant_results_xml = RESULTS_DIR / f"{variant}_results.xml"
    build_dir = BENCH_DIR / f"sim_build_{variant}"

    runner = get_runner("icarus")
    runner.build(
        verilog_sources=variant_sources(rtl_dir),
        hdl_toplevel=TOPLEVEL,
        build_dir=str(build_dir),
        always=True,
    )
    runner.test(
        hdl_toplevel=TOPLEVEL,
        test_module=TEST_MODULE,
        test_dir=str(BENCH_DIR),
        results_xml=str(variant_results_xml),
        extra_env={
            "BENCHMARK_VARIANT": variant,
            "BENCHMARK_CASES_JSON": json.dumps(cases),
            "BENCHMARK_RESULTS_JSON": str(variant_result_json),
        },
    )

    return json.loads(variant_result_json.read_text(encoding="utf-8"))


def combine_results(payloads):
    combined = []
    for payload in payloads:
        combined.extend(payload["results"])
    return combined


def add_speedups(rows):
    os_index = {
        (row["workload"], row["profile"]): row
        for row in rows
        if row["variant"] == "os"
    }
    for row in rows:
        base = os_index.get((row["workload"], row["profile"]))
        if base and row["latency_cycles"] > 0:
            row["speedup_vs_os"] = base["latency_cycles"] / row["latency_cycles"]
        else:
            row["speedup_vs_os"] = 1.0 if row["variant"] == "os" else None


def write_combined_outputs(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    combined_json = RESULTS_DIR / "combined_results.json"
    combined_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    csv_path = RESULTS_DIR / "combined_results.csv"
    fieldnames = [
        "variant",
        "workload",
        "profile",
        "M",
        "K",
        "N",
        "latency_cycles",
        "sys_busy_cycles",
        "throughput_mac_per_cycle",
        "array_utilization",
        "dma_busy_ratio",
        "memory_stall_ratio",
        "a_reads",
        "b_reads",
        "c_reads",
        "c_writes",
        "read_bytes",
        "write_bytes",
        "a_read_amplification",
        "b_read_amplification",
        "speedup_vs_os",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def print_summary(rows):
    header = (
        f"{'variant':<6} {'workload':<12} {'profile':<12} {'cycles':>8} "
        f"{'tput(MAC/cyc)':>14} {'util':>8} {'B_reads':>8} {'stall':>8} {'spd_vs_os':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        speedup = row.get("speedup_vs_os")
        speedup_str = "-" if speedup is None else f"{speedup:.3f}"
        print(
            f"{row['variant']:<6} {row['workload']:<12} {row['profile']:<12} "
            f"{row['latency_cycles']:>8} {row['throughput_mac_per_cycle']:>14.4f} "
            f"{row['array_utilization']:>8.4f} {row['b_reads']:>8} "
            f"{row['memory_stall_ratio']:>8.4f} {speedup_str:>10}"
        )


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    payloads = []
    for variant, rtl_dir in VARIANTS.items():
        payloads.append(run_variant(variant, rtl_dir, cases))

    rows = combine_results(payloads)
    add_speedups(rows)
    rows.sort(key=lambda r: (r["workload"], r["profile"], r["variant"]))
    write_combined_outputs(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()
