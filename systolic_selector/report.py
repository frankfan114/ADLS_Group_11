"""
report.py
---------
Generates a text trade-off report, a markdown report file,
and (optionally) matplotlib plots.
"""

from __future__ import annotations
from typing import Optional
import datetime
import math
import numpy as np


# ---------------------------------------------------------------------------
# Pareto front
# ---------------------------------------------------------------------------

def pareto_front(candidates: list[dict],
                 obj_a: str = "latency_cycles",
                 obj_b: str = "read_bytes") -> list[dict]:
    """
    Return the subset of candidates that are Pareto-optimal
    minimising both obj_a and obj_b.
    """
    pareto = []
    for c in candidates:
        a_c = c["metrics"][obj_a]
        b_c = c["metrics"][obj_b]
        dominated = any(
            other["metrics"][obj_a] <= a_c
            and other["metrics"][obj_b] <= b_c
            and (other["metrics"][obj_a] < a_c or other["metrics"][obj_b] < b_c)
            for other in candidates if other is not c
        )
        if not dominated:
            pareto.append(c)
    return pareto


# ---------------------------------------------------------------------------
# Confidence score display
# ---------------------------------------------------------------------------

def confidence_bar(score: float, width: int = 20) -> str:
    """ASCII progress bar for a confidence score in [0, 1]."""
    filled = round(score * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"]  {score:.2f}"


def confidence_label(score: float) -> str:
    """Short human-readable label alongside the numeric score."""
    if score >= 0.80:
        return "HIGH ✓"
    if score >= 0.45:
        return "MEDIUM ⚠"
    return "LOW ⚠⚠"


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

def generate_text_report(qM: int, qK: int, qN: int,
                         top_results: list[dict],
                         all_results: list[dict],
                         conf_info: dict = None) -> str:
    W = 70
    lines: list[str] = []

    def rule(char="─"):  lines.append(char * W)
    def blank():         lines.append("")
    def h(text):         lines.append(f"  {text}")

    lines.append("═" * W)
    h("SYSTOLIC ARRAY VARIANT SELECTION REPORT")
    lines.append("═" * W)
    blank()
    h(f"Query layer   M={qM}  K={qK}  N={qN}")
    h(f"Candidates    {len(all_results)} evaluated   │   showing top {len(top_results)}")
    blank()

    # ── TOP-K RECOMMENDATIONS ────────────────────────────────────────────
    rule()
    h("TOP-K RECOMMENDATIONS")
    rule()

    for rank, c in enumerate(top_results, 1):
        m    = c["metrics"]
        blank()
        h(f"  #{rank}  {c['variant_name']}   [{c['dim']}×{c['dim']} tiles]")
        rule("·")
        h(f"  Score          {c['score_norm']:.4f}  (normalised across all candidates)")
        h(f"  Perf score     {c.get('perf_score', 0):.4f}  │  Resource score  {c.get('resource_score', 0):.4f}")
        blank()
        h(f"  ── Performance ──────────────────────────────")
        h(f"  Latency        {m['latency_cycles']:.0f} cycles")
        h(f"  Throughput     {m['throughput_mac_per_cycle']:.4f} MAC/cycle")
        h(f"  Stall Ratio    {m['memory_stall_ratio']*100:.1f}%")
        blank()
        h(f"  ── Resource ─────────────────────────────────")
        h(f"  Active PEs     {m['physical_pe_count']:.0f}  (hardware area proxy)")
        h(f"  Read Bytes     {m['read_bytes']:.0f}  (memory bandwidth)")
        h(f"  B-reloads      {m['b_reads']:.0f}  (weight reload count)")
        blank()
        h(f"  ── Efficiency ───────────────────────────────")
        h(f"  PE Utilisation {m['pe_utilization']*100:.2f}%  (useful MACs / active PE-cycles)")
        blank()
        h(f"  ── Pipeline breakdown ───────────────────────")
        h(f"  fetch       {m['fetch_cycles']:.0f} cycles")
        h(f"  compute     {m['compute_cycles']:.0f} cycles")
        h(f"  writeback   {m['writeback_cycles']:.0f} cycles")
        blank()
        h(f"  Reference   nearest={m['nearest_layer']}  dist={m['nearest_distance']:.3f}"
          f"  ({m['ref_count']:.0f} ref point(s) used)")

    blank()

    # ── TOP-K DIRECT COMPARISON ───────────────────────────────────────────
    rule()
    h(f"TOP-{len(top_results)} TRADE-OFF COMPARISON  (relative to #1)")
    rule()
    blank()

    ref = top_results[0]
    ref_m = ref["metrics"]

    def pct(new, old):
        if old == 0:
            return "  n/a"
        d = (new - old) / abs(old) * 100
        sign = "+" if d > 0 else ""
        return f"{sign}{d:.1f}%"

    def arrow(new, old, lower_better=True):
        if old == 0:
            return ""
        better = new < old if lower_better else new > old
        return "✓" if better else "✗"

    h(f"  {'Metric':<22} {'#1 (baseline)':<18}" +
      "".join(f"  {'#'+str(i+2):<16}" for i in range(len(top_results)-1)))
    h("  " + "─" * (22 + 18 + 18 * (len(top_results)-1)))

    rows = [
        ("Latency (cycles)",    "latency_cycles",           True),
        ("Throughput (MAC/c)",  "throughput_mac_per_cycle",  False),
        ("Active PEs",          "physical_pe_count",         True),
        ("Read Bytes",          "read_bytes",                True),
        ("Stall Ratio",         "memory_stall_ratio",        True),
        ("PE Utilisation",      "pe_utilization",            False),
        ("B-reloads",           "b_reads",                   True),
    ]

    for label, metric, lower_better in rows:
        base_val = ref_m[metric]
        fmt_base = f"{base_val:.4f}" if base_val < 10 else f"{base_val:.0f}"
        row_str  = f"  {label:<22} {fmt_base:<18}"
        for other in top_results[1:]:
            val     = other["metrics"][metric]
            fmt_val = f"{val:.4f}" if val < 10 else f"{val:.0f}"
            p       = pct(val, base_val)
            a       = arrow(val, base_val, lower_better)
            row_str += f"  {fmt_val} ({p}) {a:<2}"
        h(row_str)

    blank()
    h("  ✓ = better than #1   ✗ = worse than #1")
    blank()

    # ── FULL TRADE-OFF TABLE ──────────────────────────────────────────────
    rule()
    h("FULL TRADE-OFF TABLE  (all candidates, sorted by score)")
    rule()
    blank()
    header = (f"  {'Rank':<5} {'Variant':<32} {'Dim':<6} {'Score':<7} "
              f"{'Perf':>6} {'Rsrc':>6} {'Latency':>9} {'MAC/c':>7} "
              f"{'PEs':>4} {'ReadB':>7} {'Stall%':>7}")
    h(header)
    h("  " + "─" * 80)

    for rank, c in enumerate(all_results, 1):
        m   = c["metrics"]
        tag = " ◄" if rank <= len(top_results) else ""
        row = (f"  {rank:<5} {c['variant_name']:<32} {str(c['dim'])+'×'+str(c['dim']):<6} "
               f"{c['score_norm']:<7.4f} "
               f"{c.get('perf_score', 0):>6.3f} "
               f"{c.get('resource_score', 0):>6.3f} "
               f"{m['latency_cycles']:>9.0f} "
               f"{m['throughput_mac_per_cycle']:>7.4f} "
               f"{m['physical_pe_count']:>4.0f} "
               f"{m['read_bytes']:>7.0f} "
               f"{m['memory_stall_ratio']*100:>7.1f}"
               f"{tag}")
        h(row)

    blank()

    # ── PARETO FRONT ─────────────────────────────────────────────────────
    rule()
    h("PARETO FRONT  (minimising latency AND read_bytes simultaneously)")
    rule()
    blank()

    pf = pareto_front(all_results)
    pf_sorted = sorted(pf, key=lambda c: c["metrics"]["latency_cycles"])
    h(f"  {len(pf)} Pareto-optimal configuration(s):\n")

    for c in pf_sorted:
        m = c["metrics"]
        h(f"  ●  {c['variant_name']}  [{c['dim']}×{c['dim']}]")
        h(f"     latency={m['latency_cycles']:.0f} cycles   "
          f"read={m['read_bytes']:.0f} bytes   "
          f"throughput={m['throughput_mac_per_cycle']:.4f} MAC/cycle")
        blank()

    # ── CONFIDENCE ───────────────────────────────────────────────────────
    rule()
    h("CONFIDENCE")
    rule()
    blank()
    ci = conf_info or {}
    score      = ci.get("score", 0.0)
    pred_q     = ci.get("pred_quality", 0.0)
    rank_stab  = ci.get("rank_stability", 0.0)
    score_gap  = ci.get("score_gap", 0.0)
    d_near     = ci.get("nearest_distance", 0.0)
    h(f"  Overall   {confidence_bar(score)}")
    h(f"  Level     {confidence_label(score)}")
    blank()
    h(f"  confidence  =  0.65 × pred_quality  +  0.35 × rank_stability")
    h(f"              =  0.65 × {pred_q:.3f}  +  0.35 × {rank_stab:.3f}")
    h(f"              =  {score:.4f}")
    blank()
    h(f"  pred_quality   {pred_q:.3f}   exp(−d/{2.0}) × coverage")
    h(f"    d_nearest    {d_near:.3f}   distance to closest reference layer")
    h(f"    coverage     {pred_q / max(math.exp(-d_near/2.0), 1e-9):.3f}   "
      f"0.65 + 0.35 × weighted in-range  (K=0.5, M=0.3, N=0.2)")
    blank()
    h(f"  rank_stability {rank_stab:.3f}   how clearly top-K beats the rest")
    h(f"    score_gap    {score_gap:.3f}   normalised gap between #{len(top_results)}"
      f" and #{len(top_results)+1}")
    h(f"    (gap ≥ 0.15 = clear separation → rank_stability = 1.0)")
    blank()
    h("  Reference layers in dataset:")
    h("    • mnist  M=16  K=16   N=10  (Linear)")
    h("    • bert   M=32  K=128  N=2   (Linear)")
    blank()
    h("  Predictions use physics-scaled IDW for b_reads, latency,")
    h("  fetch_cycles, read_bytes — plain IDW for remaining metrics.")
    blank()

    lines.append("═" * W)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def generate_markdown_report(qM: int, qK: int, qN: int,
                              top_results: list,
                              all_results: list,
                              w_perf: float = 0.6,
                              w_resource: float = 0.4,
                              conf_info: dict = None) -> str:
    """
    Generate a well-formatted Markdown report suitable for saving as .md file.
    Renders nicely in GitHub, VS Code, or any markdown viewer.
    """
    lines = []
    now   = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M")

    def h1(t):  lines.append(f"# {t}\n")
    def h2(t):  lines.append(f"## {t}\n")
    def h3(t):  lines.append(f"### {t}\n")
    def p(t=""):lines.append(f"{t}\n")
    def hr():   lines.append("---\n")

    # ── Header ──────────────────────────────────────────────────────────────
    h1("Systolic Array Variant Selection Report")
    p(f"**Query Layer:**  M = {qM}  |  K = {qK}  |  N = {qN}")
    p(f"**Generated:**  {now}")
    p(f"**Candidates evaluated:**  {len(all_results)}  |  **Top-K shown:**  {len(top_results)}")
    p(f"**Scoring weights:**  Performance = {w_perf:.2f}  |  Resource = {w_resource:.2f}")
    hr()

    # ── Top-K Recommendations ───────────────────────────────────────────────
    h2("Top-K Recommendations")

    for rank, c in enumerate(top_results, 1):
        m = c["metrics"]
        h3(f"#{rank} — {c['variant_name']}  [{c['dim']}×{c['dim']} tiles]")

        p(f"| Metric | Value |")
        p(f"|--------|-------|")
        p(f"| **Overall Score (normalised)** | `{c['score_norm']:.4f}` |")
        p(f"| Performance Score | `{c.get('perf_score', 0):.4f}` |")
        p(f"| Resource Score    | `{c.get('resource_score', 0):.4f}` |")
        p()

        p("**Performance**")
        p(f"| Metric | Value |")
        p(f"|--------|-------|")
        p(f"| Latency | {m['latency_cycles']:.0f} cycles |")
        p(f"| Throughput | {m['throughput_mac_per_cycle']:.4f} MAC/cycle |")
        p(f"| Memory Stall Ratio | {m['memory_stall_ratio']*100:.1f}% |")
        p()

        p("**Resource**")
        p(f"| Metric | Value |")
        p(f"|--------|-------|")
        p(f"| Active PEs | {m['physical_pe_count']:.0f} (hardware area proxy) |")
        p(f"| Read Bytes | {m['read_bytes']:.0f} (off-chip bandwidth) |")
        p(f"| B-reloads | {m['b_reads']:.0f} (weight reload count) |")
        p(f"| PE Utilisation | {m['pe_utilization']*100:.2f}% |")
        p()

        p("**Pipeline Breakdown**")
        p(f"| Stage | Cycles |")
        p(f"|-------|--------|")
        p(f"| Fetch | {m['fetch_cycles']:.0f} |")
        p(f"| Compute | {m['compute_cycles']:.0f} |")
        p(f"| Writeback | {m['writeback_cycles']:.0f} |")
        p()

        dist = m['nearest_distance']
        p(f"> **Reference:**  nearest = `{m['nearest_layer']}`  |  "
          f"distance = `{dist:.3f}`  |  "
          f"ref points used = {m['ref_count']:.0f}")
        p()

    hr()

    # ── Top-K comparison table ───────────────────────────────────────────────
    h2(f"Top-{len(top_results)} Trade-off Comparison  *(relative to #1)*")
    p()

    ref   = top_results[0]
    ref_m = ref["metrics"]

    def pct(new, old):
        if old == 0: return "n/a"
        d = (new - old) / abs(old) * 100
        sign = "+" if d > 0 else ""
        return f"{sign}{d:.1f}%"

    def sym(new, old, lower_better=True):
        if old == 0: return ""
        return "✅" if (new < old if lower_better else new > old) else "❌"

    rows = [
        ("Latency (cycles)",   "latency_cycles",            True),
        ("Throughput (MAC/c)", "throughput_mac_per_cycle",  False),
        ("Active PEs",         "physical_pe_count",          True),
        ("Read Bytes",         "read_bytes",                 True),
        ("Stall Ratio",        "memory_stall_ratio",         True),
        ("PE Utilisation",     "pe_utilization",             False),
        ("B-reloads",          "b_reads",                    True),
    ]

    # Build header
    header = "| Metric | #1 (baseline) |" + "".join(f" #{i+2} | " for i in range(len(top_results)-1))
    sep    = "|--------|--------------|" + "".join("------|" for _ in range(len(top_results)-1))
    p(header)
    p(sep)

    for label, metric, lower_better in rows:
        base = ref_m[metric]
        fmt_base = f"{base:.4f}" if base < 10 else f"{base:.0f}"
        row = f"| {label} | {fmt_base} |"
        for other in top_results[1:]:
            val = other["metrics"][metric]
            fmt_val = f"{val:.4f}" if val < 10 else f"{val:.0f}"
            row += f" {fmt_val} ({pct(val, base)}) {sym(val, base, lower_better)} |"
        p(row)

    p()
    p("> ✅ = better than #1   ❌ = worse than #1")
    p()
    hr()

    # ── Full candidate table ─────────────────────────────────────────────────
    h2("All Candidates  *(sorted by score, top-K marked)*")
    p()
    p("| Rank | Variant | Dim | Score | Perf | Rsrc | Latency | MAC/c | PEs | ReadB | Stall% |")
    p("|------|---------|-----|-------|------|------|---------|-------|-----|-------|--------|")

    for rank, c in enumerate(all_results, 1):
        m   = c["metrics"]
        tag = " ◄" if rank <= len(top_results) else ""
        p(f"| {rank}{tag} | {c['variant_name']} | {c['dim']}×{c['dim']} "
          f"| {c['score_norm']:.4f} "
          f"| {c.get('perf_score',0):.3f} "
          f"| {c.get('resource_score',0):.3f} "
          f"| {m['latency_cycles']:.0f} "
          f"| {m['throughput_mac_per_cycle']:.4f} "
          f"| {m['physical_pe_count']:.0f} "
          f"| {m['read_bytes']:.0f} "
          f"| {m['memory_stall_ratio']*100:.1f}% |")

    p()
    hr()

    # ── Pareto front ─────────────────────────────────────────────────────────
    h2("Pareto Front  *(minimising Latency AND Read Bytes simultaneously)*")
    p()

    pf = pareto_front(all_results)
    pf_sorted = sorted(pf, key=lambda c: c["metrics"]["latency_cycles"])
    p(f"{len(pf)} Pareto-optimal configuration(s):\n")
    p("| Variant | Dim | Latency | Read Bytes | Throughput |")
    p("|---------|-----|---------|------------|------------|")
    for c in pf_sorted:
        m = c["metrics"]
        p(f"| {c['variant_name']} | {c['dim']}×{c['dim']} "
          f"| {m['latency_cycles']:.0f} "
          f"| {m['read_bytes']:.0f} "
          f"| {m['throughput_mac_per_cycle']:.4f} |")
    p()
    hr()

    # ── Confidence & methodology ──────────────────────────────────────────────
    h2("Confidence & Methodology")
    p()

    ci         = conf_info or {}
    score      = ci.get("score", 0.0)
    pred_q     = ci.get("pred_quality", 0.0)
    rank_stab  = ci.get("rank_stability", 0.0)
    score_gap  = ci.get("score_gap", 0.0)
    d_near     = ci.get("nearest_distance", 0.0)

    p(f"**Confidence score: `{score:.4f}` — {confidence_label(score)}**")
    p()
    p("| Component | Formula | Value |")
    p("|-----------|---------|-------|")
    p(f"| pred_quality | exp(−d / 2.0) × coverage | `{pred_q:.4f}` |")
    p(f"| rank_stability | 0.5 + 0.5 × min(gap / 0.15, 1) | `{rank_stab:.4f}` |")
    p(f"| **confidence** | 0.65 × pred_quality + 0.35 × rank_stability | **`{score:.4f}`** |")
    p()
    p("> `pred_quality  = exp(−d_nearest / 2.0) × (0.65 + 0.35 × (0.3·in_M + 0.5·in_K + 0.2·in_N))`")
    p("> `rank_stability = 0.5 + 0.5 × min(score_gap / 0.15, 1.0)`")
    p(f"> d_nearest = `{d_near:.3f}`  |  score_gap (normalised) = `{score_gap:.3f}`")
    p("> rank_stability reflects whether the top-K ranking would hold if metric predictions shifted slightly.")
    p()
    p("**Reference layers in dataset:**")
    p()
    p("| Layer | M | K | N | Type |")
    p("|-------|---|---|---|------|")
    p("| mnist | 16 | 16 | 10 | Linear (MLP) |")
    p("| bert  | 32 | 128 | 2 | Linear (Classifier) |")
    p()
    p("> Predictions are generated via **Inverse-Distance Weighting (IDW)** "
      "over the two reference layers.")
    p("> Confidence decreases as query dimensions diverge from both references.")
    p("> A `nearest_distance` > 1.0 means the query is extrapolating — "
      "treat results with caution.")
    p()
    p("**Internal scoring sub-weights (fixed):**")
    p()
    p("*Performance score:*")
    p("| Metric | Weight |")
    p("|--------|--------|")
    p("| latency_cycles | 0.50 |")
    p("| throughput_mac_per_cycle | 0.30 |")
    p("| memory_stall_ratio | 0.20 |")
    p()
    p("*Resource score:*")
    p("| Metric | Weight |")
    p("|--------|--------|")
    p("| physical_pe_count | 0.40 |")
    p("| read_bytes | 0.30 |")
    p("| b_reads | 0.20 |")
    p("| pe_utilization | 0.10 |")
    p()
    p(f"**Final score formula:**  "
      f"`score = {w_perf:.2f} × perf_score + {w_resource:.2f} × resource_score`")
    p()

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optional matplotlib plots
# ---------------------------------------------------------------------------

def plot_tradeoff(all_results: list[dict],
                  top_results: list[dict],
                  save_path: Optional[str] = None) -> None:
    """
    Scatter plot: latency (x) vs read_bytes (y).
    Top-K candidates are highlighted.
    Pareto front is connected with a dashed line.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("[report] matplotlib not installed — skipping plot")
        return

    COLOURS = {
        "OS":     "#4C72B0",
        "WS":     "#DD8452",
        "OS_PP":  "#55A868",
        "WS_PP":  "#C44E52",
        "RSA_WS": "#8172B3",
    }
    MARKERS = {4: "o", 8: "s", 16: "^"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    top_keys  = {(c["variant"], c["dim"]) for c in top_results}
    pf_keys   = {(c["variant"], c["dim"]) for c in pareto_front(all_results)}

    # ── Left: latency vs read_bytes ───────────────────────────────────
    ax = axes[0]
    for c in all_results:
        m     = c["metrics"]
        key   = (c["variant"], c["dim"])
        color = COLOURS.get(c["variant"], "grey")
        msize = 120 if key in top_keys else 60
        edge  = "black" if key in top_keys else color
        lw    = 2.0 if key in top_keys else 0.5
        ax.scatter(m["latency_cycles"], m["read_bytes"],
                   s=msize, c=color, edgecolors=edge, linewidths=lw,
                   marker=MARKERS.get(c["dim"], "o"), zorder=3)
        ax.annotate(f"{c['variant']}\n{c['dim']}×{c['dim']}",
                    (m["latency_cycles"], m["read_bytes"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=6.5, alpha=0.8)

    # Draw Pareto front
    pf_pts = sorted(
        [c for c in all_results if (c["variant"], c["dim"]) in pf_keys],
        key=lambda c: c["metrics"]["latency_cycles"]
    )
    if pf_pts:
        px = [c["metrics"]["latency_cycles"] for c in pf_pts]
        py = [c["metrics"]["read_bytes"]     for c in pf_pts]
        ax.plot(px, py, "k--", linewidth=1, alpha=0.5, label="Pareto front", zorder=2)

    ax.set_xlabel("Latency (cycles)", fontsize=10)
    ax.set_ylabel("Read Bytes", fontsize=10)
    ax.set_title("Latency vs Memory Traffic", fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Legend by variant
    patches = [mpatches.Patch(color=v, label=k) for k, v in COLOURS.items()]
    ax.legend(handles=patches, fontsize=7, loc="upper right")

    # ── Right: throughput vs PE utilisation ──────────────────────────
    ax = axes[1]
    for c in all_results:
        m     = c["metrics"]
        key   = (c["variant"], c["dim"])
        color = COLOURS.get(c["variant"], "grey")
        msize = 120 if key in top_keys else 60
        edge  = "black" if key in top_keys else color
        lw    = 2.0 if key in top_keys else 0.5
        ax.scatter(m["throughput_mac_per_cycle"], m["pe_utilization"] * 100,
                   s=msize, c=color, edgecolors=edge, linewidths=lw,
                   marker=MARKERS.get(c["dim"], "o"), zorder=3)
        ax.annotate(f"{c['variant']}\n{c['dim']}×{c['dim']}",
                    (m["throughput_mac_per_cycle"], m["pe_utilization"] * 100),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=6.5, alpha=0.8)

    ax.set_xlabel("Throughput (MAC/cycle)", fontsize=10)
    ax.set_ylabel("PE Utilisation (%)", fontsize=10)
    ax.set_title("Throughput vs PE Utilisation", fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Dim legend
    dim_handles = [
        plt.scatter([], [], marker=MARKERS[d], c="grey", s=60, label=f"{d}×{d} tiles")
        for d in MARKERS
    ]
    ax.legend(handles=dim_handles, fontsize=7, loc="lower right")

    plt.suptitle("Systolic Array Variant Trade-off Analysis", fontsize=13, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[report] Plot saved to {save_path}")
    else:
        plt.show()
