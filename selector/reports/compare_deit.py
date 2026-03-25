"""
compare_deit.py  —  Predicted vs Actual trade-off comparison
DeiT layer (M=64, K=192, N=10)  |  RSA-WS 4×4  vs  WS 16×16
"""

import sys, copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FixedLocator, FixedFormatter

sys.path.insert(0, "/Users/lovekrissa/Desktop/ADL_Group_11/systolic_selector")
from loader import load_reference_data
from selector import select_top_k, score_all_candidates

# ---------------------------------------------------------------------------
# Run selector — all 11 predicted candidates (same normalisation as report)
# ---------------------------------------------------------------------------

CSV_DIR = "/Users/lovekrissa/Desktop/ADL_Group_11/benchmark_csv"
records = load_reference_data(CSV_DIR)
_, all_pred, _ = select_top_k(64, 192, 10, records, top_k=2, w_perf=0.6, w_resource=0.4)

# ---------------------------------------------------------------------------
# Actual Vivado measurements
# ---------------------------------------------------------------------------

ACTUAL_METRICS = {
    ("RSA_WS", 4): dict(
        latency_cycles=377333, throughput_mac_per_cycle=0.3257,
        memory_stall_ratio=0.6961, physical_pe_count=16,
        read_bytes=39168, b_reads=576, pe_utilization=0.0204,
        fetch_cycles=0, compute_cycles=0, writeback_cycles=0,
    ),
    ("WS", 16): dict(
        latency_cycles=127520, throughput_mac_per_cycle=0.9636,
        memory_stall_ratio=0.7687, physical_pe_count=64,
        read_bytes=14592, b_reads=1600, pe_utilization=0.0151,
        fetch_cycles=0, compute_cycles=0, writeback_cycles=0,
    ),
}

all_actual = copy.deepcopy(all_pred)
for cand in all_actual:
    key = (cand["variant"], cand["dim"])
    if key in ACTUAL_METRICS:
        for m, v in ACTUAL_METRICS[key].items():
            cand["metrics"][m] = v
        cand["metrics"].pop("_norm", None)

score_all_candidates(all_actual, w_perf=0.6, w_resource=0.4)
raw = np.array([c["score"] for c in all_actual])
lo, hi = raw.min(), raw.max()
for c, r in zip(all_actual, raw):
    c["score_norm"] = float((r - lo) / (hi - lo)) if hi > lo else 0.5

def find(pool, variant, dim):
    return next(c for c in pool if c["variant"] == variant and c["dim"] == dim)

p_rsa = find(all_pred,   "RSA_WS", 4)
p_ws  = find(all_pred,   "WS",    16)
a_rsa = find(all_actual, "RSA_WS", 4)
a_ws  = find(all_actual, "WS",    16)

perf_sc = [p_rsa["perf_score"], p_ws["perf_score"],
           a_rsa["perf_score"], a_ws["perf_score"]]
rsrc_sc = [p_rsa["resource_score"], p_ws["resource_score"],
           a_rsa["resource_score"], a_ws["resource_score"]]
overall = [p_rsa["score"], p_ws["score"],
           a_rsa["score"], a_ws["score"]]

# ---------------------------------------------------------------------------
# Advantage ratios
# ---------------------------------------------------------------------------

METRICS = [
    ("latency_cycles",           "Latency",     True),
    ("throughput_mac_per_cycle", "Throughput",  False),
    ("memory_stall_ratio",       "Stall Ratio", True),
    ("physical_pe_count",        "PE Count",    True),
    ("read_bytes",               "Read Bytes",  True),
    ("b_reads",                  "B-reloads",   True),
    ("pe_utilization",           "PE Util",     False),
]

def adv(rsa, ws, lib): return (ws / rsa) if lib else (rsa / ws)

PRED_RAW    = {k: p_rsa["metrics"][k] for k, _, _ in METRICS}
PRED_RAW_WS = {k: p_ws["metrics"][k]  for k, _, _ in METRICS}
ACT_RSA     = ACTUAL_METRICS[("RSA_WS", 4)]
ACT_WS      = ACTUAL_METRICS[("WS", 16)]

pred_r = [adv(PRED_RAW[k], PRED_RAW_WS[k], l) for k, _, l in METRICS]
act_r  = [adv(ACT_RSA[k],  ACT_WS[k],      l) for k, _, l in METRICS]
labels = [lbl for _, lbl, _ in METRICS]

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right": False,
})

fig = plt.figure(figsize=(17, 6.5))
fig.patch.set_facecolor("white")
gs  = GridSpec(1, 2, figure=fig, wspace=0.42, left=0.06, right=0.97,
               top=0.88, bottom=0.14)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

fig.suptitle(
    "DeiT Layer (M=64, K=192, N=10) — Predicted vs Actual Trade-off\n"
    "RSA-WS 4×4  vs  WS 16×16",
    fontsize=13, fontweight="bold", y=1.00
)

# ── colours ───────────────────────────────────────────────────────────────
# Left panel: green = RSA wins, red = WS wins; solid fill = predicted, hatch = actual
GREEN = "#66BB6A"   # RSA wins
RED   = "#EF9A9A"   # WS wins

# Right panel: one color per config, shape encodes predicted vs actual
COL_RSA = "#5C6BC0"   # indigo  — RSA-WS 4×4
COL_WS  = "#EF6C00"   # orange  — WS 16×16

# ============================================================
# PANEL 1 — advantage ratio, log scale
# ============================================================

x = np.arange(len(labels))
W = 0.32

for i, (pr, ar) in enumerate(zip(pred_r, act_r)):
    c = GREEN if pr >= 1 else RED   # colour by who wins (predicted direction)
    ca = GREEN if ar >= 1 else RED

    # predicted bar — solid fill, full opacity
    ax1.bar(x[i] - W/2, pr, width=W,
            color=c, edgecolor="#555555", linewidth=0.6,
            alpha=1.0, zorder=3)
    # actual bar — hatched, slightly transparent
    ax1.bar(x[i] + W/2, ar, width=W,
            color=ca, edgecolor="#555555", linewidth=0.6,
            hatch="////", alpha=0.55, zorder=3)

    # value labels — dark text just outside the bar top/bottom
    def label_bar(xpos, val):
        if val >= 1:
            ax1.text(xpos, val * 1.12, f"{val:.2f}",
                     ha="center", va="bottom",
                     fontsize=8, fontweight="bold", color="#222222", zorder=5)
        else:
            ax1.text(xpos, val * 0.89, f"{val:.2f}",
                     ha="center", va="top",
                     fontsize=8, fontweight="bold", color="#222222", zorder=5)

    label_bar(x[i] - W/2, pr)
    label_bar(x[i] + W/2, ar)

    # ✓ / ✗ above the taller bar
    correct = (pr >= 1) == (ar >= 1)
    sym     = "✓" if correct else "✗"
    sym_col = "#2E7D32" if correct else "#C62828"
    top_y   = max(pr, ar) * 1.65
    ax1.text(x[i], top_y, sym, ha="center", va="center",
             fontsize=12, color=sym_col, fontweight="bold", zorder=6)

ax1.axhline(1.0, color="#444444", lw=1.2, ls="--", zorder=2)
ax1.axhspan(1.0, 12,  alpha=0.04, color="#4CAF50", zorder=1)
ax1.axhspan(0.08, 1.0, alpha=0.04, color="#F44336", zorder=1)

# "RSA wins ▲" / "WS wins ▼" text labels on the shaded regions
ax1.text(len(labels) - 0.45, 2.5, "RSA wins ▲",
         color="#2E7D32", fontsize=8.5, va="center", style="italic", zorder=4)
ax1.text(len(labels) - 0.45, 0.55, "WS wins ▼",
         color="#C62828", fontsize=8.5, va="center", style="italic", zorder=4)

ax1.set_yscale("log")
ax1.set_ylim(0.1, 10)
ax1.yaxis.set_major_locator(FixedLocator([0.1, 0.2, 0.33, 0.5, 1.0, 2.0, 4.0, 10.0]))
ax1.yaxis.set_major_formatter(FixedFormatter(["0.1","0.2","0.33","0.5","1.0","2.0","4.0","10"]))
ax1.yaxis.set_minor_locator(plt.NullLocator())
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=10)
ax1.set_ylabel("RSA 4×4 advantage ratio  (log scale)", fontsize=10.5)
ax1.set_title(
    "RSA advantage ratio per metric\n"
    "> 1 = RSA 4×4 wins   |   < 1 = WS 16×16 wins",
    fontsize=10, pad=8
)
ax1.set_facecolor("white")
ax1.grid(axis="y", color="#DDDDDD", linewidth=0.7, zorder=0)

# legend — 2 entries only (Predicted solid / Actual hatched)
legend_elems = [
    mpatches.Patch(facecolor="#AAAAAA", edgecolor="#555555",
                   linewidth=0.6, label="Predicted"),
    mpatches.Patch(facecolor="#AAAAAA", edgecolor="#555555",
                   linewidth=0.6, hatch="////", label="Actual"),
]
ax1.legend(handles=legend_elems, fontsize=9, loc="upper left",
           framealpha=0.9, handlelength=1.4)

n_ok = sum((p >= 1) == (a >= 1) for p, a in zip(pred_r, act_r))
ax1.set_xlabel(
    f"Direction accuracy: {n_ok}/{len(labels)}  "
    + "  ".join("✓" if (p>=1)==(a>=1) else "✗"
                for p, a in zip(pred_r, act_r)),
    fontsize=9.5, labelpad=6
)

# ============================================================
# PANEL 2 — Perf vs Resource trade-off space
# ============================================================

ax2.set_facecolor("white")
ax2.grid(color="#DDDDDD", linewidth=0.7, zorder=0)
ax2.set_xlim(-0.05, 1.05)
ax2.set_ylim(-0.05, 1.05)

# arrows: predicted → actual, coloured per config
for pi, ai, col in [(0, 2, COL_RSA), (1, 3, COL_WS)]:
    ax2.annotate(
        "",
        xy=(perf_sc[ai], rsrc_sc[ai]),
        xytext=(perf_sc[pi], rsrc_sc[pi]),
        arrowprops=dict(arrowstyle="-|>", color=col, lw=1.8,
                        mutation_scale=16,
                        connectionstyle="arc3,rad=0.2"),
        zorder=3
    )

# predicted — triangle (▲), same config colour
ax2.scatter(perf_sc[0], rsrc_sc[0], s=300, c=COL_RSA,
            marker="^", alpha=0.55, edgecolors="white", linewidths=1.5, zorder=4)
ax2.scatter(perf_sc[1], rsrc_sc[1], s=300, c=COL_WS,
            marker="^", alpha=0.55, edgecolors="white", linewidths=1.5, zorder=4)

# actual — square (■), same config colour
ax2.scatter(perf_sc[2], rsrc_sc[2], s=200, c=COL_RSA,
            marker="s", alpha=0.95, edgecolors="white", linewidths=1.5, zorder=5)
ax2.scatter(perf_sc[3], rsrc_sc[3], s=200, c=COL_WS,
            marker="s", alpha=0.95, edgecolors="white", linewidths=1.5, zorder=5)

# point labels — plain text near each point, no box
LABEL_CFG = [
    (perf_sc[0], rsrc_sc[0], "RSA 4×4\n(predicted)",  COL_RSA, -0.13,  0.07),
    (perf_sc[1], rsrc_sc[1], "WS 16×16\n(predicted)", COL_WS,   0.13,  0.07),
    (perf_sc[2], rsrc_sc[2], "RSA 4×4\n(actual)",     COL_RSA, -0.13, -0.07),
    (perf_sc[3], rsrc_sc[3], "WS 16×16\n(actual)",    COL_WS,   0.13, -0.07),
]
for px, py, txt, col, dx, dy in LABEL_CFG:
    ax2.annotate(
        txt, xy=(px, py), xytext=(px + dx, py + dy),
        fontsize=8.5, color=col, fontweight="semibold",
        ha="center", va="center",
        arrowprops=dict(arrowstyle="-", color=col, lw=0.6),
        zorder=7
    )

# corner labels
ax2.text(0.98, 0.98, "Fast &\nresource-lean", transform=ax2.transAxes,
         ha="right", va="top", fontsize=8, color="#888888", style="italic")
ax2.text(0.02, 0.02, "Slow &\nresource-heavy", transform=ax2.transAxes,
         ha="left", va="bottom", fontsize=8, color="#888888", style="italic")


ax2.set_xlabel("Performance score  (higher = faster, less stall)", fontsize=10.5, labelpad=6)
ax2.set_ylabel("Resource score  (higher = fewer PEs, less bandwidth)", fontsize=10.5)
ax2.set_title(
    "Perf vs Resource trade-off space\n"
    "Normalised across all 11 candidates  —  arrows = prediction error",
    fontsize=10, pad=8
)

# legend: triangle=predicted, square=actual; colour patches per config
legend_pts = [
    plt.scatter([], [], s=120, c="#888888", marker="^", alpha=0.6,  label="Predicted"),
    plt.scatter([], [], s=90,  c="#888888", marker="s", alpha=0.95, label="Actual"),
    mpatches.Patch(color=COL_RSA, label="RSA-WS 4×4"),
    mpatches.Patch(color=COL_WS,  label="WS 16×16"),
]
ax2.legend(handles=legend_pts, fontsize=8.5, loc="upper left",
           framealpha=0.9, ncol=2, columnspacing=0.8)

# ---------------------------------------------------------------------------
out = "/Users/lovekrissa/Desktop/ADL_Group_11/reports/compare_deit.png"
plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
print(f"Saved → {out}")
plt.close()
