# Systolic Array Variant Selection Report

**Query Layer:**  M = 64  |  K = 192  |  N = 10

**Generated:**  2026-03-25  03:13

**Candidates evaluated:**  11  |  **Top-K shown:**  2

**Scoring weights:**  Performance = 0.60  |  Resource = 0.40

---

## Top-K Recommendations

### #1 — Weight Stationary  [16×16 tiles]

| Metric | Value |

|--------|-------|

| **Overall Score (normalised)** | `1.0000` |

| Performance Score | `0.8550` |

| Resource Score    | `0.5246` |



**Performance**

| Metric | Value |

|--------|-------|

| Latency | 153414 cycles |

| Throughput | 0.8010 MAC/cycle |

| Memory Stall Ratio | 74.3% |



**Resource**

| Metric | Value |

|--------|-------|

| Active PEs | 64 (hardware area proxy) |

| Read Bytes | 16016 (off-chip bandwidth) |

| B-reloads | 105 (weight reload count) |

| PE Utilisation | 0.46% |



**Pipeline Breakdown**

| Stage | Cycles |

|-------|--------|

| Fetch | 132780 |

| Compute | 390 |

| Writeback | 736 |



> **Reference:**  nearest = `bert`  |  distance = `0.746`  |  ref points used = 2



### #2 — Output Stationary  [16×16 tiles]

| Metric | Value |

|--------|-------|

| **Overall Score (normalised)** | `0.9535` |

| Performance Score | `0.8274` |

| Resource Score    | `0.4898` |



**Performance**

| Metric | Value |

|--------|-------|

| Latency | 162929 cycles |

| Throughput | 0.7542 MAC/cycle |

| Memory Stall Ratio | 74.2% |



**Resource**

| Metric | Value |

|--------|-------|

| Active PEs | 64 (hardware area proxy) |

| Read Bytes | 17113 (off-chip bandwidth) |

| B-reloads | 197 (weight reload count) |

| PE Utilisation | 0.44% |



**Pipeline Breakdown**

| Stage | Cycles |

|-------|--------|

| Fetch | 142226 |

| Compute | 412 |

| Writeback | 736 |



> **Reference:**  nearest = `bert`  |  distance = `0.746`  |  ref points used = 2



---

## Top-2 Trade-off Comparison  *(relative to #1)*



| Metric | #1 (baseline) | #2 | 

|--------|--------------|------|

| Latency (cycles) | 153414 | 162929 (+6.2%) ❌ |

| Throughput (MAC/c) | 0.8010 | 0.7542 (-5.8%) ❌ |

| Active PEs | 64 | 64 (0.0%) ❌ |

| Read Bytes | 16016 | 17113 (+6.9%) ❌ |

| Stall Ratio | 0.7434 | 0.7420 (-0.2%) ✅ |

| PE Utilisation | 0.0046 | 0.0044 (-5.1%) ❌ |

| B-reloads | 105 | 197 (+87.0%) ❌ |



> ✅ = better than #1   ❌ = worse than #1



---

## All Candidates  *(sorted by score, top-K marked)*



| Rank | Variant | Dim | Score | Perf | Rsrc | Latency | MAC/c | PEs | ReadB | Stall% |

|------|---------|-----|-------|------|------|---------|-------|-----|-------|--------|

| 1 ◄ | Weight Stationary | 16×16 | 1.0000 | 0.855 | 0.525 | 153414 | 0.8010 | 64 | 16016 | 74.3% |

| 2 ◄ | Output Stationary | 16×16 | 0.9535 | 0.827 | 0.490 | 162929 | 0.7542 | 64 | 17113 | 74.2% |

| 3 | Reconfigurable WS (SARA) | 4×4 | 0.8864 | 0.507 | 0.861 | 425169 | 0.2890 | 16 | 42787 | 68.6% |

| 4 | Reconfigurable WS (SARA) | 8×8 | 0.7216 | 0.602 | 0.448 | 275881 | 0.4454 | 64 | 29401 | 73.2% |

| 5 | Weight Stationary | 8×8 | 0.6649 | 0.554 | 0.427 | 298692 | 0.4114 | 64 | 32031 | 73.6% |

| 6 | Weight Stationary + Ping-Pong | 4×4 | 0.5573 | 0.473 | 0.372 | 430129 | 0.2857 | 64 | 42787 | 69.7% |

| 7 | Output Stationary | 8×8 | 0.5108 | 0.465 | 0.307 | 356865 | 0.3443 | 64 | 38617 | 73.8% |

| 8 | Output Stationary + Ping-Pong | 8×8 | 0.4625 | 0.412 | 0.308 | 345102 | 0.3561 | 64 | 38617 | 76.5% |

| 9 | Weight Stationary | 4×4 | 0.4611 | 0.405 | 0.316 | 494791 | 0.2483 | 64 | 50677 | 69.4% |

| 10 | Output Stationary | 4×4 | 0.0239 | 0.138 | 0.000 | 701704 | 0.1751 | 64 | 73728 | 71.1% |

| 11 | Output Stationary + Ping-Pong | 4×4 | 0.0000 | 0.112 | 0.000 | 687211 | 0.1788 | 64 | 73728 | 72.7% |



---

## Pareto Front  *(minimising Latency AND Read Bytes simultaneously)*



1 Pareto-optimal configuration(s):


| Variant | Dim | Latency | Read Bytes | Throughput |

|---------|-----|---------|------------|------------|

| Weight Stationary | 16×16 | 153414 | 16016 | 0.8010 |



---

## Confidence & Methodology



**Confidence score: `0.5756` — MEDIUM ⚠**



| Component | Formula | Value |

|-----------|---------|-------|

| pred_quality | exp(−d / 2.0) × coverage | `0.4958` |

| rank_stability | 0.5 + 0.5 × min(gap / 0.15, 1) | `0.7237` |

| **confidence** | 0.65 × pred_quality + 0.35 × rank_stability | **`0.5756`** |



> `pred_quality  = exp(−d_nearest / 2.0) × (0.65 + 0.35 × (0.3·in_M + 0.5·in_K + 0.2·in_N))`

> `rank_stability = 0.5 + 0.5 × min(score_gap / 0.15, 1.0)`

> d_nearest = `0.746`  |  score_gap (normalised) = `0.067`

> rank_stability reflects whether the top-K ranking would hold if metric predictions shifted slightly.



**Reference layers in dataset:**



| Layer | M | K | N | Type |

|-------|---|---|---|------|

| mnist | 16 | 16 | 10 | Linear (MLP) |

| bert  | 32 | 128 | 2 | Linear (Classifier) |



> Predictions are generated via **Inverse-Distance Weighting (IDW)** over the two reference layers.

> Confidence decreases as query dimensions diverge from both references.

> A `nearest_distance` > 1.0 means the query is extrapolating — treat results with caution.



**Internal scoring sub-weights (fixed):**



*Performance score:*

| Metric | Weight |

|--------|--------|

| latency_cycles | 0.50 |

| throughput_mac_per_cycle | 0.30 |

| memory_stall_ratio | 0.20 |



*Resource score:*

| Metric | Weight |

|--------|--------|

| physical_pe_count | 0.40 |

| read_bytes | 0.30 |

| b_reads | 0.20 |

| pe_utilization | 0.10 |



**Final score formula:**  `score = 0.60 × perf_score + 0.40 × resource_score`


