"""
selector.py
-----------
Nearest-neighbour variant and dimension selector.

Scoring model
-------------
  score = w_perf * perf_score  +  w_resource * resource_score

  perf_score and resource_score are each a fixed weighted combination
  of normalised metrics.  Only w_perf / w_resource are exposed to the
  user — the internal sub-weights are fixed reasonable defaults.

  Performance sub-weights  (sum = 1.0):
    latency_cycles          0.50   primary speed signal
    throughput_mac_per_cycle 0.30   compute efficiency
    memory_stall_ratio      0.20   how memory-bound the config is

  Resource sub-weights  (sum = 1.0):
    physical_pe_count       0.40   hardware area proxy (fewer = better)
    read_bytes              0.30   off-chip bandwidth consumed
    b_reads                 0.20   weight reload count (WS vs OS diff.)
    pe_utilization          0.10   useful work per active PE-cycle

Distance weighting rationale
-----------------------------
  K  (reduction dim)  → directly scales weight-load cycles → w=0.5
  M  (output rows)    → drives reuse in WS variants         → w=0.3
  N  (output cols)    → affects PE column utilisation        → w=0.2
"""

from __future__ import annotations
from typing import Optional
import math
import numpy as np
from loader import PERF_METRICS

# ---------------------------------------------------------------------------
# Variant display names
# ---------------------------------------------------------------------------

VARIANT_DISPLAY = {
    "OS":     "Output Stationary",
    "WS":     "Weight Stationary",
    "OS_PP":  "Output Stationary + Ping-Pong",
    "WS_PP":  "Weight Stationary + Ping-Pong",
    "RSA_WS": "Reconfigurable WS (SARA)",
}

# ---------------------------------------------------------------------------
# Internal fixed sub-weights  (not exposed to the user)
# ---------------------------------------------------------------------------

# Performance sub-weights — sum = 1.0
_PERF_SW = {
    "latency_cycles":           0.50,
    "throughput_mac_per_cycle": 0.30,
    "memory_stall_ratio":       0.20,
}

# Resource sub-weights — sum = 1.0
_RESOURCE_SW = {
    "physical_pe_count": 0.40,
    "read_bytes":        0.30,
    "b_reads":           0.20,
    "pe_utilization":    0.10,
}

# Metrics where LOWER is better (inverted during normalisation)
_LOWER_IS_BETTER = {
    "latency_cycles", "memory_stall_ratio",
    "read_bytes", "b_reads", "physical_pe_count",
}

# ---------------------------------------------------------------------------
# User-facing default top-level weights
# ---------------------------------------------------------------------------

DEFAULT_PERF_W     = 0.5   # performance side
DEFAULT_RESOURCE_W = 0.5   # resource side

# ---------------------------------------------------------------------------
# Dimension weights for the distance function
# ---------------------------------------------------------------------------

_DIM_W = {"M": 0.3, "K": 0.5, "N": 0.2}


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------

def layer_distance(qM: int, qK: int, qN: int,
                   rM: int, rK: int, rN: int) -> float:
    """
    Weighted log-scale distance between two layers.

      d = sqrt( w_M*(log(M_q+1) - log(M_r+1))^2
              + w_K*(log(K_q+1) - log(K_r+1))^2
              + w_N*(log(N_q+1) - log(N_r+1))^2 )
    """
    diffs = np.array([
        np.log1p(qM) - np.log1p(rM),
        np.log1p(qK) - np.log1p(rK),
        np.log1p(qN) - np.log1p(rN),
    ])
    w = np.array([_DIM_W["M"], _DIM_W["K"], _DIM_W["N"]])
    return float(np.sqrt(np.dot(w, diffs ** 2)))


# ---------------------------------------------------------------------------
# Physics-informed scaling
# ---------------------------------------------------------------------------
#
# Three metrics grow super-linearly with layer size and cannot be reliably
# predicted by flat IDW blending alone.  For each we derive a scale factor
# from the hardware execution model and apply it to the reference value
# *before* the IDW blend, so the blend operates on already-scaled values.
#
#   b_reads / latency_cycles / fetch_cycles / read_bytes
#       driver: 3-D tile product = M-tiles × K-tiles × N-tiles
#       All four metrics scale with the total number of tile operations
#       the array executes across all three output dimensions.
#       scale  = ceil(qM/dim)·ceil(qK/dim)·ceil(qN/dim)
#              / ceil(rM/dim)·ceil(rK/dim)·ceil(rN/dim)

def _physics_scale(metric: str,
                   ref_val: float,
                   qM: int, qK: int, qN: int,
                   rM: int, rK: int, rN: int,
                   dim: int) -> float:
    """Return ref_val scaled to query dims using hardware physics."""
    if metric in ("latency_cycles", "fetch_cycles", "read_bytes"):
        # 3-D tile product: M-tiles × K-tiles × N-tiles
        # These metrics scale with total tile operations across all dimensions.
        q_tiles = math.ceil(qM / dim) * math.ceil(qK / dim) * math.ceil(qN / dim)
        r_tiles = math.ceil(rM / dim) * math.ceil(rK / dim) * math.ceil(rN / dim)
        return ref_val * (q_tiles / r_tiles) if r_tiles > 0 else ref_val

    # b_reads: plain IDW — both reference layers show equal b_reads across
    # variants (RSA_WS = WS = 128 on BERT, 48 on MNIST), so tile scaling
    # produces a wrong-direction cross-variant signal. Plain IDW is more honest.
    return ref_val


# Metrics that get physics scaling before the IDW blend
_PHYSICS_SCALED = {"latency_cycles", "fetch_cycles", "read_bytes"}


# ---------------------------------------------------------------------------
# Prediction via inverse-distance weighting
# ---------------------------------------------------------------------------

def predict_for_candidate(variant: str, dim: int,
                           qM: int, qK: int, qN: int,
                           records: list) -> Optional[dict]:
    """
    Predict all metrics for (variant, dim) given query layer dims.

    For metrics in _PHYSICS_SCALED each reference value is first scaled to
    the query's tile/memory footprint before the IDW blend.  This corrects
    the super-linear growth of b_reads / latency / read_bytes that plain IDW
    severely underestimates when extrapolating beyond the reference range.

    Returns None if no reference data exists for this (variant, dim).
    """
    matches = [r for r in records
               if r["variant"] == variant and r["dim"] == dim]
    if not matches:
        return None

    distances = np.array([
        layer_distance(qM, qK, qN, r["M_ref"], r["K_ref"], r["N_ref"])
        for r in matches
    ])

    if np.any(distances == 0.0):
        idw = np.where(distances == 0.0, 1.0, 0.0)
    else:
        idw = 1.0 / distances
    idw = idw / idw.sum()

    predicted = {}
    for metric in PERF_METRICS:
        if metric in _PHYSICS_SCALED:
            # Scale each reference value to query dims before blending
            vals = np.array([
                _physics_scale(metric,
                               r.get(metric, 0.0),
                               qM, qK, qN,
                               r["M_ref"], r["K_ref"], r["N_ref"],
                               dim)
                for r in matches
            ], dtype=float)
        else:
            vals = np.array([r.get(metric, 0.0) for r in matches], dtype=float)

        predicted[metric] = float(np.dot(idw, vals))

    # Throughput is physically defined as total_MACs / latency.
    # Deriving it from the predicted latency keeps it consistent
    # and avoids the IDW blend underestimating the gap.
    total_ops = qM * qK * qN
    if predicted.get("latency_cycles", 0) > 0:
        predicted["throughput_mac_per_cycle"] = total_ops / predicted["latency_cycles"]

    nearest_idx = int(np.argmin(distances))
    predicted["nearest_layer"]    = matches[nearest_idx]["layer_ref"]
    predicted["nearest_distance"] = float(distances[nearest_idx])
    predicted["ref_count"]        = len(matches)

    return predicted


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _normalise(values: np.ndarray) -> np.ndarray:
    lo, hi = values.min(), values.max()
    if hi > lo:
        return (values - lo) / (hi - lo)
    return np.full_like(values, 0.5, dtype=float)


def score_all_candidates(candidates: list,
                          w_perf: float,
                          w_resource: float) -> list:
    """
    Two-level scoring:

      score = w_perf * perf_score  +  w_resource * resource_score

    perf_score and resource_score are each computed from fixed internal
    sub-weights applied to normalised metrics.  Each sub-score lives in
    [0, 1] before the top-level weights are applied.

    Parameters
    ----------
    candidates  : list of candidate dicts (modified in-place)
    w_perf      : user weight for the performance side
    w_resource  : user weight for the resource side
    """
    # Normalise every metric across all candidates
    norm = {}
    for m in PERF_METRICS:
        vals = np.array([c["metrics"][m] for c in candidates], dtype=float)
        n    = _normalise(vals)
        # invert so that "lower is better" metrics score higher when low
        norm[m] = 1.0 - n if m in _LOWER_IS_BETTER else n

    # Store per-candidate normalised values
    for i, c in enumerate(candidates):
        c["metrics"]["_norm"] = {m: float(norm[m][i]) for m in PERF_METRICS}

    # Compute two-level scores
    for c in candidates:
        n = c["metrics"]["_norm"]

        perf_score = sum(
            _PERF_SW[m] * n[m] for m in _PERF_SW
        )

        resource_score = sum(
            _RESOURCE_SW[m] * n[m] for m in _RESOURCE_SW
        )

        c["perf_score"]     = perf_score
        c["resource_score"] = resource_score
        c["score"]          = w_perf * perf_score + w_resource * resource_score

    return candidates


# ---------------------------------------------------------------------------
# Confidence score
# ---------------------------------------------------------------------------

def _pred_quality(qM: int, qK: int, qN: int, records: list) -> tuple:
    """
    Prediction quality component of the confidence score.

    pred_quality = exp(−d_nearest / τ) × (floor + (1−floor) × weighted_coverage)

      τ     = 2.0   soft decay — penalises distance but not harshly
      floor = 0.65  minimum coverage so extrapolation is never crippling
      weighted_coverage uses the same K=0.5 / M=0.3 / N=0.2 weights as distance

    Returns (pred_quality, d_nearest).
    """
    _TAU   = 2.0
    _FLOOR = 0.65

    distances = [
        layer_distance(qM, qK, qN, r["M_ref"], r["K_ref"], r["N_ref"])
        for r in records
    ]
    d_nearest = min(distances)
    proximity = math.exp(-d_nearest / _TAU)

    ref_M_vals = [r["M_ref"] for r in records]
    ref_K_vals = [r["K_ref"] for r in records]
    ref_N_vals = [r["N_ref"] for r in records]

    in_M = 1.0 if min(ref_M_vals) <= qM <= max(ref_M_vals) else 0.0
    in_K = 1.0 if min(ref_K_vals) <= qK <= max(ref_K_vals) else 0.0
    in_N = 1.0 if min(ref_N_vals) <= qN <= max(ref_N_vals) else 0.0

    weighted_in_range = (
        _DIM_W["M"] * in_M +
        _DIM_W["K"] * in_K +
        _DIM_W["N"] * in_N
    )
    coverage = _FLOOR + (1.0 - _FLOOR) * weighted_in_range

    return proximity * coverage, d_nearest


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def select_top_k(qM: int, qK: int, qN: int,
                 records: list,
                 top_k: int      = 3,
                 w_perf: float   = DEFAULT_PERF_W,
                 w_resource: float = DEFAULT_RESOURCE_W) -> tuple:
    """
    Parameters
    ----------
    qM, qK, qN   : query layer dimensions
    records      : reference data from loader.load_reference_data()
    top_k        : number of top results to return
    w_perf       : weight on performance score  (0–1)
    w_resource   : weight on resource score     (0–1)
                   w_perf + w_resource should sum to 1

    Returns
    -------
    top_results  : top-K ranked candidates
    all_results  : all candidates sorted by score (for trade-off report)
    """
    # Collect unique (variant, dim) pairs
    seen, pairs = set(), []
    for r in records:
        key = (r["variant"], r["dim"])
        if key not in seen:
            seen.add(key)
            pairs.append(key)
    pairs.sort()

    candidates, skipped = [], []
    for variant, dim in pairs:
        metrics = predict_for_candidate(variant, dim, qM, qK, qN, records)
        if metrics is None:
            skipped.append((variant, dim))
            continue
        candidates.append({
            "variant":      variant,
            "dim":          dim,
            "variant_name": VARIANT_DISPLAY.get(variant, variant),
            "metrics":      metrics,
            "score":        0.0,
        })

    if skipped:
        print(f"[selector] Skipped {len(skipped)} pair(s) with no reference data")

    if not candidates:
        raise ValueError("No candidates evaluated — check csv_dir path.")

    score_all_candidates(candidates, w_perf, w_resource)
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Normalise final scores to [0, 1] for display
    scores      = np.array([c["score"] for c in candidates])
    norm_scores = _normalise(scores)
    for c, ns in zip(candidates, norm_scores):
        c["score_norm"] = float(ns)

    # ── Confidence score ─────────────────────────────────────────────────
    # Component 1: prediction quality (proximity + coverage)
    pred_q, d_nearest = _pred_quality(qM, qK, qN, records)

    # Component 2: ranking stability — how clearly are the top-K separated
    # from the first excluded candidate?
    # score_gap = (score_K − score_{K+1}) normalised by total score range
    _GAP_SCALE = 0.15   # gap threshold considered "good separation"
    if len(candidates) > top_k:
        gap_raw    = candidates[top_k - 1]["score_norm"] - candidates[top_k]["score_norm"]
        score_range = candidates[0]["score_norm"] - candidates[-1]["score_norm"]
        norm_gap   = gap_raw / (score_range + 1e-9)
        rank_stab  = 0.5 + 0.5 * min(norm_gap / _GAP_SCALE, 1.0)
    else:
        norm_gap  = 1.0
        rank_stab = 1.0

    # Weighted blend: prediction quality matters more (0.65) but
    # ranking stability reflects whether the top-K choice is trustworthy (0.35)
    confidence = 0.65 * pred_q + 0.35 * rank_stab

    conf_info = {
        "score":          round(confidence, 4),
        "pred_quality":   round(pred_q,    4),
        "rank_stability": round(rank_stab, 4),
        "score_gap":      round(norm_gap,  4),
        "nearest_distance": round(d_nearest, 4),
    }

    return candidates[:top_k], candidates, conf_info
