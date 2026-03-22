import json
import math
import statistics
from pathlib import Path

from cocotb_tools.runner import get_runner


ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "benchmark"
RESULTS_DIR = BENCH_DIR / "results"
TOPLEVEL = "matrix_top_wrapper"
TEST_MODULE = "systolic_axi_benchmark_tb"


VARIANTS = {
    "ws": ROOT / "weight_stationary" / "matrix",
    "sara_ws": ROOT / "sara_ws" / "matrix",
}


MEMORY_PROFILES = {
    "moderate": {
        "wait_prob": 0.10,
        "max_wait": 3,
    },
    "constrained": {
        "wait_prob": 0.20,
        "max_wait": 4,
    },
}


SHAPE_SWEEP = [
    {"case_group": "square_exact", "shape_tag": "square_exact", "M": 8, "K": 8, "N": 8},
    {"case_group": "square_ragged", "shape_tag": "square_ragged", "M": 15, "K": 10, "N": 13},
    {"case_group": "tall_skinny", "shape_tag": "tall_skinny", "M": 32, "K": 8, "N": 3},
    {"case_group": "wide_short", "shape_tag": "wide_short", "M": 3, "K": 8, "N": 32},
    {"case_group": "small_batch_large_channel", "shape_tag": "small_batch_large_channel", "M": 2, "K": 32, "N": 32},
    {"case_group": "irregular_small", "shape_tag": "irregular_small", "M": 5, "K": 11, "N": 7},
]


LAYER_SWEEP = [
    {"case_group": "early_conv_like", "shape_tag": "early_conv_like", "M": 64, "K": 27, "N": 16},
    {"case_group": "pointwise_like", "shape_tag": "pointwise_like", "M": 49, "K": 32, "N": 64},
    {"case_group": "bottleneck_like", "shape_tag": "bottleneck_like", "M": 16, "K": 64, "N": 24},
    {"case_group": "late_stage_like", "shape_tag": "late_stage_like", "M": 4, "K": 64, "N": 128},
]


BANDWIDTH_SWEEP = [
    {"case_group": "bw_tall_skinny", "shape_tag": "bw_tall_skinny", "M": 32, "K": 8, "N": 3},
    {"case_group": "bw_pointwise_like", "shape_tag": "bw_pointwise_like", "M": 49, "K": 32, "N": 64},
    {"case_group": "bw_small_batch_large_channel", "shape_tag": "bw_small_batch_large_channel", "M": 2, "K": 32, "N": 32},
]


CONFIG_SWEEP_SHAPES = [
    {"case_group": "cfg_tall_3x16", "shape_tag": "cfg_tall_3x16", "M": 3, "K": 8, "N": 16},
    {"case_group": "cfg_wide_16x3", "shape_tag": "cfg_wide_16x3", "M": 16, "K": 8, "N": 3},
    {"case_group": "cfg_tiny_2x2", "shape_tag": "cfg_tiny_2x2", "M": 2, "K": 8, "N": 2},
    {"case_group": "cfg_tradeoff_5x7", "shape_tag": "cfg_tradeoff_5x7", "M": 5, "K": 11, "N": 7},
]


SARA_CONFIGS = [
    {"config_mode": "manual_8x8", "auto_config_en": False, "manual_row_mask": 0xFF, "manual_col_mask": 0xFF},
    {"config_mode": "manual_4x8", "auto_config_en": False, "manual_row_mask": 0x0F, "manual_col_mask": 0xFF},
    {"config_mode": "manual_8x4", "auto_config_en": False, "manual_row_mask": 0xFF, "manual_col_mask": 0x0F},
    {"config_mode": "manual_4x4", "auto_config_en": False, "manual_row_mask": 0x0F, "manual_col_mask": 0x0F},
    {"config_mode": "manual_2x8", "auto_config_en": False, "manual_row_mask": 0x03, "manual_col_mask": 0xFF},
    {"config_mode": "manual_8x2", "auto_config_en": False, "manual_row_mask": 0xFF, "manual_col_mask": 0x03},
    {"config_mode": "manual_2x2", "auto_config_en": False, "manual_row_mask": 0x03, "manual_col_mask": 0x03},
    {"config_mode": "auto", "auto_config_en": True, "manual_row_mask": 0xFF, "manual_col_mask": 0xFF},
]


def variant_sources(rtl_dir: Path):
    return sorted([str(p) for p in rtl_dir.rglob("*.sv")] + [str(p) for p in rtl_dir.rglob("*.v")])


def make_case(*, suite, profile, seed, config_mode="fixed_8x8", auto_config_en=None, manual_row_mask=None, manual_col_mask=None, **shape):
    case = {
        "case_name": f"{suite}__{shape['case_group']}__{config_mode}__{profile}",
        "workload": shape["case_group"],
        "suite": suite,
        "case_group": shape["case_group"],
        "shape_tag": shape["shape_tag"],
        "profile": profile,
        "M": shape["M"],
        "K": shape["K"],
        "N": shape["N"],
        "data_mode": "random",
        "seed": seed,
        "memory": MEMORY_PROFILES[profile],
        "config_mode": config_mode,
    }
    if auto_config_en is not None:
        case["auto_config_en"] = auto_config_en
    if manual_row_mask is not None:
        case["manual_row_mask"] = manual_row_mask
    if manual_col_mask is not None:
        case["manual_col_mask"] = manual_col_mask
    return case


def build_cases_for_variant(variant: str):
    seed = 3000
    cases = []

    def add_case(**kwargs):
        nonlocal seed
        cases.append(make_case(seed=seed, **kwargs))
        seed += 1

    common_config_mode = "auto" if variant == "sara_ws" else "fixed_8x8"
    common_auto_flag = True if variant == "sara_ws" else None

    for shape in SHAPE_SWEEP:
        add_case(suite="shape_sweep", profile="moderate", config_mode=common_config_mode, auto_config_en=common_auto_flag, **shape)

    for shape in LAYER_SWEEP:
        add_case(suite="layer_sweep", profile="moderate", config_mode=common_config_mode, auto_config_en=common_auto_flag, **shape)

    for shape in BANDWIDTH_SWEEP:
        add_case(suite="bandwidth_sweep", profile="constrained", config_mode=common_config_mode, auto_config_en=common_auto_flag, **shape)

    if variant == "ws":
        for shape in CONFIG_SWEEP_SHAPES:
            add_case(suite="config_gain", profile="moderate", config_mode="fixed_8x8", **shape)
    elif variant == "sara_ws":
        for shape in CONFIG_SWEEP_SHAPES:
            for cfg in SARA_CONFIGS:
                add_case(suite="config_gain", profile="moderate", **cfg, **shape)

    return cases


def run_variant(variant: str, rtl_dir: Path, cases):
    variant_result_json = RESULTS_DIR / f"{variant}_flexibility_results.json"
    variant_results_xml = RESULTS_DIR / f"{variant}_flexibility_results.xml"
    build_dir = BENCH_DIR / f"sim_build_flex_{variant}"

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


def ratio(num, den):
    if den == 0:
        return None
    return num / den


def pct_delta(new, old):
    if old == 0:
        return None
    return ((new - old) / old) * 100.0


def summarize_metric(rows, metric):
    values = [row[metric] for row in rows]
    if not values:
        return {}
    return {
        "mean": statistics.fmean(values),
        "min": min(values),
        "max": max(values),
        "std": statistics.pstdev(values) if len(values) > 1 else 0.0,
    }


def analyze_common_pairs(rows):
    ws_rows = {
        (row["suite"], row["case_group"], row["profile"]): row
        for row in rows
        if row["variant"] == "ws" and row["suite"] in {"shape_sweep", "layer_sweep", "bandwidth_sweep"}
    }
    sara_rows = {
        (row["suite"], row["case_group"], row["profile"]): row
        for row in rows
        if row["variant"] == "sara_ws" and row["suite"] in {"shape_sweep", "layer_sweep", "bandwidth_sweep"}
    }

    comparisons = []
    for key, ws_row in ws_rows.items():
        sara_row = sara_rows.get(key)
        if not sara_row:
            continue
        comparisons.append({
            "suite": ws_row["suite"],
            "case_group": ws_row["case_group"],
            "profile": ws_row["profile"],
            "M": ws_row["M"],
            "K": ws_row["K"],
            "N": ws_row["N"],
            "ws_latency_cycles": ws_row["latency_cycles"],
            "sara_latency_cycles": sara_row["latency_cycles"],
            "latency_delta_pct": pct_delta(sara_row["latency_cycles"], ws_row["latency_cycles"]),
            "ws_cycles_per_mac": ws_row["cycles_per_mac"],
            "sara_cycles_per_mac": sara_row["cycles_per_mac"],
            "cycles_per_mac_delta_pct": pct_delta(sara_row["cycles_per_mac"], ws_row["cycles_per_mac"]),
            "ws_array_utilization": ws_row["array_utilization"],
            "sara_array_utilization": sara_row["array_utilization"],
            "array_utilization_delta_pct": pct_delta(sara_row["array_utilization"], ws_row["array_utilization"]),
            "ws_mapping_efficiency": ws_row["mapping_efficiency"],
            "sara_mapping_efficiency": sara_row["mapping_efficiency"],
            "mapping_efficiency_delta_pct": pct_delta(sara_row["mapping_efficiency"], ws_row["mapping_efficiency"]),
            "ws_output_slot_utilization": ws_row["output_slot_utilization"],
            "sara_output_slot_utilization": sara_row["output_slot_utilization"],
            "output_slot_utilization_delta_pct": pct_delta(sara_row["output_slot_utilization"], ws_row["output_slot_utilization"]),
            "ws_bytes_per_mac": ws_row["bytes_per_mac"],
            "sara_bytes_per_mac": sara_row["bytes_per_mac"],
            "bytes_per_mac_delta_pct": pct_delta(sara_row["bytes_per_mac"], ws_row["bytes_per_mac"]),
            "ws_b_read_amplification": ws_row["b_read_amplification"],
            "sara_b_read_amplification": sara_row["b_read_amplification"],
            "b_read_amplification_delta_pct": pct_delta(sara_row["b_read_amplification"], ws_row["b_read_amplification"]),
            "ws_memory_stall_ratio": ws_row["memory_stall_ratio"],
            "sara_memory_stall_ratio": sara_row["memory_stall_ratio"],
            "memory_stall_delta_pct": pct_delta(sara_row["memory_stall_ratio"], ws_row["memory_stall_ratio"]),
            "sara_selected_cfg_id": sara_row["selected_cfg_id"],
            "sara_selected_active_rows": sara_row["selected_active_rows"],
            "sara_selected_active_cols": sara_row["selected_active_cols"],
        })
    return comparisons


def analyze_stability(rows):
    focus_rows = [row for row in rows if row["suite"] in {"shape_sweep", "layer_sweep"}]
    summary = {}
    for variant in {"ws", "sara_ws"}:
        variant_rows = [row for row in focus_rows if row["variant"] == variant]
        summary[variant] = {
            "count": len(variant_rows),
            "cycles_per_mac": summarize_metric(variant_rows, "cycles_per_mac"),
            "array_utilization": summarize_metric(variant_rows, "array_utilization"),
            "mapping_efficiency": summarize_metric(variant_rows, "mapping_efficiency"),
            "output_slot_utilization": summarize_metric(variant_rows, "output_slot_utilization"),
            "bytes_per_mac": summarize_metric(variant_rows, "bytes_per_mac"),
        }
    return summary


def analyze_config_gain(rows):
    ws_rows = {
        row["shape_tag"]: row
        for row in rows
        if row["variant"] == "ws" and row["suite"] == "config_gain"
    }
    sara_rows = [
        row for row in rows
        if row["variant"] == "sara_ws" and row["suite"] == "config_gain"
    ]

    summary = []
    for shape_tag in sorted({row["shape_tag"] for row in sara_rows}):
        group_rows = [row for row in sara_rows if row["shape_tag"] == shape_tag]
        auto_row = next(row for row in group_rows if row["config_mode"] == "auto")
        manual_rows = [row for row in group_rows if row["config_mode"] != "auto"]
        best_mapping = max(manual_rows, key=lambda row: row["mapping_efficiency"])
        worst_mapping = min(manual_rows, key=lambda row: row["mapping_efficiency"])
        best_latency = min(manual_rows, key=lambda row: row["latency_cycles"])
        ws_row = ws_rows.get(shape_tag)

        summary.append({
            "shape_tag": shape_tag,
            "M": auto_row["M"],
            "K": auto_row["K"],
            "N": auto_row["N"],
            "ws_fixed_latency_cycles": ws_row["latency_cycles"] if ws_row else None,
            "ws_fixed_mapping_efficiency": ws_row["mapping_efficiency"] if ws_row else None,
            "auto_cfg_id": auto_row["selected_cfg_id"],
            "auto_config_mode": auto_row["config_mode"],
            "auto_latency_cycles": auto_row["latency_cycles"],
            "auto_mapping_efficiency": auto_row["mapping_efficiency"],
            "auto_output_slot_utilization": auto_row["output_slot_utilization"],
            "best_mapping_config": best_mapping["config_mode"],
            "best_mapping_efficiency": best_mapping["mapping_efficiency"],
            "worst_mapping_config": worst_mapping["config_mode"],
            "worst_mapping_efficiency": worst_mapping["mapping_efficiency"],
            "best_latency_config": best_latency["config_mode"],
            "best_latency_cycles": best_latency["latency_cycles"],
            "auto_vs_mapping_oracle_gap_pct": pct_delta(auto_row["mapping_efficiency"], best_mapping["mapping_efficiency"]),
            "auto_vs_latency_oracle_gap_pct": pct_delta(auto_row["latency_cycles"], best_latency["latency_cycles"]),
            "best_mapping_gain_vs_ws_pct": pct_delta(best_mapping["mapping_efficiency"], ws_row["mapping_efficiency"]) if ws_row else None,
            "auto_mapping_gain_vs_ws_pct": pct_delta(auto_row["mapping_efficiency"], ws_row["mapping_efficiency"]) if ws_row else None,
        })
    return summary


def build_overall_summary(rows):
    pairwise = analyze_common_pairs(rows)
    stability = analyze_stability(rows)
    config_gain = analyze_config_gain(rows)

    def suite_average(metric, suite):
        values = [row[metric] for row in pairwise if row["suite"] == suite and row[metric] is not None]
        return statistics.fmean(values) if values else None

    return {
        "pairwise_common": pairwise,
        "stability": stability,
        "config_gain": config_gain,
        "suite_averages": {
            "shape_sweep": {
                "latency_delta_pct_mean": suite_average("latency_delta_pct", "shape_sweep"),
                "mapping_efficiency_delta_pct_mean": suite_average("mapping_efficiency_delta_pct", "shape_sweep"),
                "output_slot_utilization_delta_pct_mean": suite_average("output_slot_utilization_delta_pct", "shape_sweep"),
                "bytes_per_mac_delta_pct_mean": suite_average("bytes_per_mac_delta_pct", "shape_sweep"),
            },
            "layer_sweep": {
                "latency_delta_pct_mean": suite_average("latency_delta_pct", "layer_sweep"),
                "mapping_efficiency_delta_pct_mean": suite_average("mapping_efficiency_delta_pct", "layer_sweep"),
                "output_slot_utilization_delta_pct_mean": suite_average("output_slot_utilization_delta_pct", "layer_sweep"),
                "bytes_per_mac_delta_pct_mean": suite_average("bytes_per_mac_delta_pct", "layer_sweep"),
            },
            "bandwidth_sweep": {
                "memory_stall_delta_pct_mean": suite_average("memory_stall_delta_pct", "bandwidth_sweep"),
                "bytes_per_mac_delta_pct_mean": suite_average("bytes_per_mac_delta_pct", "bandwidth_sweep"),
                "b_read_amplification_delta_pct_mean": suite_average("b_read_amplification_delta_pct", "bandwidth_sweep"),
            },
        },
    }


def format_pct(value):
    if value is None:
        return "-"
    return f"{value:+.1f}%"


def format_float(value, digits=4):
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def render_markdown_summary(summary):
    lines = []
    lines.append("# SARA-WS Flexibility Benchmark Summary")
    lines.append("")
    lines.append("## Common Case Comparison")
    lines.append("")
    lines.append("| Suite | Case | Shape | Latency Delta | Mapping Eff Delta | Output Slot Delta | Bytes/MAC Delta | SARA Config |")
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | --- |")
    for row in summary["pairwise_common"]:
        lines.append(
            f"| {row['suite']} | {row['case_group']} | {row['M']}x{row['K']}x{row['N']} | "
            f"{format_pct(row['latency_delta_pct'])} | "
            f"{format_pct(row['mapping_efficiency_delta_pct'])} | "
            f"{format_pct(row['output_slot_utilization_delta_pct'])} | "
            f"{format_pct(row['bytes_per_mac_delta_pct'])} | "
            f"{row['sara_selected_active_rows']}x{row['sara_selected_active_cols']} (cfg {row['sara_selected_cfg_id']}) |"
        )

    lines.append("")
    lines.append("## Stability Summary")
    lines.append("")
    lines.append("| Variant | Mean cycles/MAC | Worst cycles/MAC | Mean mapping eff | Min mapping eff | Mapping eff std | Mean bytes/MAC |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for variant, data in summary["stability"].items():
        lines.append(
            f"| {variant} | "
            f"{format_float(data['cycles_per_mac'].get('mean'))} | "
            f"{format_float(data['cycles_per_mac'].get('max'))} | "
            f"{format_float(data['mapping_efficiency'].get('mean'))} | "
            f"{format_float(data['mapping_efficiency'].get('min'))} | "
            f"{format_float(data['mapping_efficiency'].get('std'))} | "
            f"{format_float(data['bytes_per_mac'].get('mean'))} |"
        )

    lines.append("")
    lines.append("## Config Space Gain")
    lines.append("")
    lines.append("| Shape | Auto cfg | Auto map eff | Best map cfg | Best map eff | Worst map cfg | Worst map eff | Best latency cfg | Auto vs best map | Auto vs best latency |")
    lines.append("| --- | --- | ---: | --- | ---: | --- | ---: | --- | ---: | ---: |")
    for row in summary["config_gain"]:
        lines.append(
            f"| {row['shape_tag']} ({row['M']}x{row['K']}x{row['N']}) | "
            f"{row['auto_cfg_id']} | "
            f"{format_float(row['auto_mapping_efficiency'])} | "
            f"{row['best_mapping_config']} | "
            f"{format_float(row['best_mapping_efficiency'])} | "
            f"{row['worst_mapping_config']} | "
            f"{format_float(row['worst_mapping_efficiency'])} | "
            f"{row['best_latency_config']} | "
            f"{format_pct(row['auto_vs_mapping_oracle_gap_pct'])} | "
            f"{format_pct(row['auto_vs_latency_oracle_gap_pct'])} |"
        )

    lines.append("")
    return "\n".join(lines)


def write_outputs(rows, summary):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RESULTS_DIR / "flexibility_combined_results.json"
    raw_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    summary_path = RESULTS_DIR / "flexibility_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    markdown_path = RESULTS_DIR / "flexibility_summary.md"
    markdown_path.write_text(render_markdown_summary(summary), encoding="utf-8")


def print_console_summary(summary):
    print("Flexibility benchmark summary")
    print("----------------------------")
    for suite, values in summary["suite_averages"].items():
        print(
            f"{suite:<16} "
            f"latency={format_pct(values.get('latency_delta_pct_mean')):<8} "
            f"map_eff={format_pct(values.get('mapping_efficiency_delta_pct_mean')):<8} "
            f"slot_util={format_pct(values.get('output_slot_utilization_delta_pct_mean')):<8} "
            f"bytes/MAC={format_pct(values.get('bytes_per_mac_delta_pct_mean')):<8}"
        )

    print("")
    print("Stability")
    for variant, data in summary["stability"].items():
        print(
            f"{variant:<8} "
            f"worst cycles/MAC={format_float(data['cycles_per_mac'].get('max')):<8} "
            f"min map_eff={format_float(data['mapping_efficiency'].get('min')):<8} "
            f"map_eff std={format_float(data['mapping_efficiency'].get('std')):<8} "
            f"mean bytes/MAC={format_float(data['bytes_per_mac'].get('mean')):<8}"
        )


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    payloads = []
    for variant, rtl_dir in VARIANTS.items():
        cases = build_cases_for_variant(variant)
        payload = run_variant(variant, rtl_dir, cases)
        payloads.append(payload)

    rows = combine_results(payloads)
    rows.sort(key=lambda row: (row["suite"], row["case_group"], row["variant"], row["config_mode"]))
    summary = build_overall_summary(rows)
    write_outputs(rows, summary)
    print_console_summary(summary)


if __name__ == "__main__":
    main()
