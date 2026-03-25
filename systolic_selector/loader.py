"""
loader.py
---------
Loads all 22 benchmark CSV files and attaches metadata
(variant, dim, reference layer M/K/N) parsed from filenames.
"""

import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Manual filename → metadata mapping
# (filenames are inconsistent so we hard-code rather than parse)
# ---------------------------------------------------------------------------
FILE_METADATA = {
    # --- OUTPUT STATIONARY (OS) ---
    "os+4+minst.csv":                                       {"variant": "OS",     "dim": 4,  "layer": "mnist"},
    "os+8+minst.csv":                                       {"variant": "OS",     "dim": 8,  "layer": "mnist"},
    "os+16+minst.csv":                                      {"variant": "OS",     "dim": 16, "layer": "mnist"},
    "os+bert+444.csv":                                      {"variant": "OS",     "dim": 4,  "layer": "bert"},
    "os+bert+888.csv":                                      {"variant": "OS",     "dim": 8,  "layer": "bert"},
    "os+bert+16.csv":                                       {"variant": "OS",     "dim": 16, "layer": "bert"},

    # --- WEIGHT STATIONARY, no ping-pong (WS) ---
    "ws_nopp+MINST+4.csv":                                  {"variant": "WS",     "dim": 4,  "layer": "mnist"},
    "ws_nopp+MINST+8.csv":                                  {"variant": "WS",     "dim": 8,  "layer": "mnist"},
    "ws_nopp+MINST+16.csv":                                 {"variant": "WS",     "dim": 16, "layer": "mnist"},
    "ws+nopp k=4m=4n=4,berttiny.csv":                       {"variant": "WS",     "dim": 4,  "layer": "bert"},
    "ws+nopp N=8M=8 32x128x2 bert.csv":                     {"variant": "WS",     "dim": 8,  "layer": "bert"},
    "ws+nopp k=16m=16n=16,berttiny.csv":                    {"variant": "WS",     "dim": 16, "layer": "bert"},

    # --- OS with ping-pong (OS_PP) ---
    "os+pp_mnist_mlp_w8_qat_raw_16x16x10 44.csv":           {"variant": "OS_PP",  "dim": 4,  "layer": "mnist"},
    "os+pp_mnist_mlp_w8_qat_raw_16x16x10 88.csv":           {"variant": "OS_PP",  "dim": 8,  "layer": "mnist"},
    "os+pp_bert_case0_32x128x2 44.csv":                     {"variant": "OS_PP",  "dim": 4,  "layer": "bert"},
    "os+pp_bert_case0_32x128x2 88.csv":                     {"variant": "OS_PP",  "dim": 8,  "layer": "bert"},

    # --- WS with ping-pong (WS_PP) ---
    "ws+pp mnist_mlp_w8_qat_raw_int32 44 16x16x10.csv":     {"variant": "WS_PP",  "dim": 4,  "layer": "mnist"},
    "ws+pp N=4M=4 32x128x2 bert 44.csv":                    {"variant": "WS_PP",  "dim": 4,  "layer": "bert"},

    # --- Reconfigurable WS / SARA (RSA_WS) ---
    "rsa_ws_minst_layer_4_4_16x16x10.csv":                  {"variant": "RSA_WS", "dim": 4,  "layer": "mnist"},
    "rsa_ws_minst_layer_8_8_16x16x10.csv":                  {"variant": "RSA_WS", "dim": 8,  "layer": "mnist"},
    "rsa_ws_layer_4_4_32x128x2.csv":                        {"variant": "RSA_WS", "dim": 4,  "layer": "bert"},
    "rsa_ws_layer_8_8_32x128x2.csv":                        {"variant": "RSA_WS", "dim": 8,  "layer": "bert"},
}

# Reference layer ground-truth dimensions
LAYER_INFO = {
    # Both are nn.Linear layers — "mlp" referred to the model, not the layer op
    "mnist": {"M": 16, "K": 16,  "N": 10, "type": "linear"},
    "bert":  {"M": 32, "K": 128, "N": 2,  "type": "linear"},
}

# Metrics we care about (from the CSV)
PERF_METRICS = [
    "latency_cycles",
    "throughput_mac_per_cycle",
    "pe_utilization",
    "memory_stall_ratio",
    "read_bytes",
    "b_reads",
    "fetch_cycles",
    "compute_cycles",
    "writeback_cycles",
    "physical_pe_count",
]


def load_reference_data(csv_dir: str) -> list[dict]:
    """
    Load all benchmark CSVs.

    Returns a list of records, each containing:
        variant, dim, layer_ref, M_ref, K_ref, N_ref, type_ref
        + all numeric columns from the CSV row
    """
    csv_dir = Path(csv_dir)
    records  = []
    missing  = []

    for fname, meta in FILE_METADATA.items():
        fpath = csv_dir / fname
        if not fpath.exists():
            missing.append(fname)
            continue

        layer_key  = meta["layer"]
        layer_info = LAYER_INFO[layer_key]

        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = {
                    "variant":    meta["variant"],
                    "dim":        meta["dim"],
                    "layer_ref":  layer_key,
                    "M_ref":      layer_info["M"],
                    "K_ref":      layer_info["K"],
                    "N_ref":      layer_info["N"],
                    "type_ref":   layer_info["type"],
                    "source_file": fname,
                }
                for col, val in row.items():
                    try:
                        record[col] = float(val)
                    except (ValueError, TypeError):
                        record[col] = val
                records.append(record)

    if missing:
        print(f"[loader] Warning: {len(missing)} file(s) not found — {missing}")

    print(f"[loader] Loaded {len(records)} reference records from {len(records)} files")
    return records
