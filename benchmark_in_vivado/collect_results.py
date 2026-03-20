import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "benchmark_results.csv"
DEFAULT_JSON = ROOT / "benchmark_results.json"
DEFAULT_LOG = ROOT / "xsim.log"

NUMERIC_INT_FIELDS = {
    "case_id",
    "M",
    "K",
    "N",
    "preload_ps",
    "cfg_ps",
    "run_ps",
    "readback_ps",
    "useful_macs",
    "latency_cycles",
    "sys_busy_cycles",
    "dma_busy_cycles",
    "axi_active_cycles",
    "ar_requests",
    "aw_requests",
    "read_beats",
    "write_beats",
    "b_responses",
    "a_reads",
    "b_reads",
    "c_reads",
    "c_writes",
    "read_bytes",
    "write_bytes",
    "mismatch_count",
}

NUMERIC_FLOAT_FIELDS = {
    "dma_busy_ratio",
    "axi_active_ratio",
    "throughput_mac_per_cycle",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect Vivado benchmark results from CSV or XSim log."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Input CSV or log file. Defaults to benchmark_results.csv, then xsim.log.",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=DEFAULT_JSON,
        help="Where to write normalized JSON output.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional normalized CSV output path. Useful when parsing a log.",
    )
    return parser.parse_args()


def pick_input(path_arg: Path | None) -> Path:
    if path_arg is not None:
        return path_arg
    if DEFAULT_CSV.exists():
        return DEFAULT_CSV
    if DEFAULT_LOG.exists():
        return DEFAULT_LOG
    raise FileNotFoundError(
        "No input file found. Expected benchmark_results.csv or xsim.log in benchmark_in_vivado."
    )


def convert_value(key: str, value: str):
    if key in NUMERIC_INT_FIELDS:
        return int(value)
    if key in NUMERIC_FLOAT_FIELDS:
        return float(value)
    return value


def normalize_row(row: dict[str, str]) -> dict:
    normalized = {}
    for key, value in row.items():
        if value is None or value == "":
            normalized[key] = value
        else:
            normalized[key] = convert_value(key, value)

    normalized.setdefault("status", "PASS")
    normalized.setdefault("case_name", f"case_{normalized.get('case_id', 'unknown')}")
    normalized.setdefault("workload", normalized["case_name"])
    return normalized


def load_csv_rows(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [normalize_row(row) for row in reader]


def parse_bench_line(line: str) -> dict | None:
    if "BENCH_RESULT," not in line:
        return None
    payload = line.split("BENCH_RESULT,", 1)[1].strip()
    result = {}
    for token in payload.split(","):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        result[key.strip()] = value.strip()

    if not result:
        return None

    alias_map = {
        "case": "case_id",
        "m": "M",
        "k": "K",
        "n": "N",
        "run_cycles": "latency_cycles",
        "busy_cycles": "sys_busy_cycles",
        "macs_per_run_cycle": "throughput_mac_per_cycle",
        "ar": "ar_requests",
        "aw": "aw_requests",
        "r": "read_beats",
        "w": "write_beats",
        "b": "b_responses",
    }
    aliased = {}
    for key, value in result.items():
        aliased[alias_map.get(key, key)] = value

    if "read_bytes" not in aliased and "read_beats" in aliased:
        aliased["read_bytes"] = str(int(aliased["read_beats"]) * 4)
    if "write_bytes" not in aliased and "write_beats" in aliased:
        aliased["write_bytes"] = str(int(aliased["write_beats"]) * 4)

    return normalize_row(aliased)


def load_log_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parsed = parse_bench_line(line)
        if parsed is not None:
            rows.append(parsed)
    return rows


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        return load_csv_rows(path)
    return load_log_rows(path)


def write_json(path: Path, rows: list[dict], source: Path):
    payload = {
        "source": str(source),
        "results": rows,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_summary(rows: list[dict]):
    if not rows:
        print("No BENCH_RESULT rows found.")
        return

    header = (
        f"{'case':<6} {'status':<8} {'M':>4} {'K':>4} {'N':>4} "
        f"{'cycles':>10} {'busy':>10} {'dma':>10} {'tput':>12} {'B_reads':>10}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row.get('case_id', '-'):>6} {row.get('status', '-'):>8} "
            f"{row.get('M', 0):>4} {row.get('K', 0):>4} {row.get('N', 0):>4} "
            f"{row.get('latency_cycles', 0):>10} {row.get('sys_busy_cycles', 0):>10} "
            f"{row.get('dma_busy_cycles', 0):>10} {row.get('throughput_mac_per_cycle', 0.0):>12.4f} "
            f"{row.get('b_reads', 0):>10}"
        )


def main():
    args = parse_args()
    input_path = pick_input(args.input)
    rows = load_rows(input_path)
    write_json(args.json_out, rows, input_path)
    if args.csv_out is not None:
        write_csv(args.csv_out, rows)
    print_summary(rows)
    print(f"Wrote JSON results to {args.json_out}")
    if args.csv_out is not None:
        print(f"Wrote CSV results to {args.csv_out}")


if __name__ == "__main__":
    main()
