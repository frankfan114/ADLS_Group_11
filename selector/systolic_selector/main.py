"""
main.py
-------
CLI entry point for the systolic array variant selector.

Reports are automatically saved to the  reports/  folder:
  reports/report_M{M}_K{K}_N{N}.md   — full markdown report
  reports/report_M{M}_K{K}_N{N}.txt  — plain-text version
  reports/plot_M{M}_K{K}_N{N}.png    — trade-off scatter plot

With --generate, patched RTL folders are created under:
  reports/generated_rtl/rank1_{VARIANT}_dim{D}/
  reports/generated_rtl/rank2_{VARIANT}_dim{D}/
  ...

Usage examples
--------------
# BERT-tiny layer (closest to reference)
python main.py --M 32 --K 128 --N 2

# MNIST MLP layer
python main.py --M 16 --K 16 --N 10

# Custom layer, latency-first priority, top-5
python main.py --M 64 --K 192 --N 10 --perf_w 0.8 --resource_w 0.2 --top_k 5

# Suppress the auto-plot window
python main.py --M 32 --K 128 --N 2 --no_plot

# Skip RTL generation
python main.py --M 64 --K 192 --N 10 --no_generate
"""

import argparse
import sys
from pathlib import Path

# Ensure sibling modules are importable when called from any directory
sys.path.insert(0, str(Path(__file__).parent))

from loader    import load_reference_data
from selector  import select_top_k, DEFAULT_PERF_W, DEFAULT_RESOURCE_W
from report    import generate_text_report, generate_markdown_report, plot_tradeoff
from generator import generate_rtl

DEFAULT_CSV_DIR  = Path(__file__).parent.parent / "benchmark_csv"
DEFAULT_OUT_DIR  = Path(__file__).parent.parent / "reports"
DEFAULT_RTL_DIR  = Path(__file__).parent.parent.parent / "rtl"


def parse_args():
    p = argparse.ArgumentParser(
        description="Nearest-neighbour systolic array variant selector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Layer spec
    p.add_argument("--M",    type=int, required=True,
                   help="Matrix M dimension  (output rows / batch)")
    p.add_argument("--K",    type=int, required=True,
                   help="Matrix K dimension  (reduction / input features)")
    p.add_argument("--N",    type=int, required=True,
                   help="Matrix N dimension  (output columns / neurons)")

    # Top-level user weights
    p.add_argument("--perf_w",     type=float, default=DEFAULT_PERF_W,
                   help=f"Weight on the performance score  0–1  (default {DEFAULT_PERF_W})")
    p.add_argument("--resource_w", type=float, default=DEFAULT_RESOURCE_W,
                   help=f"Weight on the resource score     0–1  (default {DEFAULT_RESOURCE_W})")

    # Selector options
    p.add_argument("--top_k",    type=int, default=2,
                   help="Number of top recommendations (default 3)")
    p.add_argument("--csv_dir",  type=str, default=str(DEFAULT_CSV_DIR),
                   help="Path to folder containing benchmark CSV files")

    # Output options
    p.add_argument("--out_dir",  type=str, default=str(DEFAULT_OUT_DIR),
                   help="Directory to save report and plot (default: reports/)")
    p.add_argument("--no_plot",  action="store_true",
                   help="Disable trade-off scatter plot")

    # RTL generator options
    p.add_argument("--no_generate", action="store_true",
                   help="Disable RTL generation for top-K selections")
    p.add_argument("--rtl_dir",  type=str, default=str(DEFAULT_RTL_DIR),
                   help="Path to root RTL folder (default: ../../rtl relative to selector/)")

    return p.parse_args()


def normalise_weights(perf_w: float, resource_w: float):
    """Ensure the two top-level weights sum to 1."""
    total = perf_w + resource_w
    if abs(total - 1.0) > 0.01:
        print(f"[main] Weights sum to {total:.3f} — normalising to 1.0")
    return perf_w / total, resource_w / total


def main():
    args = parse_args()

    w_perf, w_resource = normalise_weights(args.perf_w, args.resource_w)

    # ── Output directory ──────────────────────────────────────────────────
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"M{args.M}_K{args.K}_N{args.N}"

    # ── Load reference data ───────────────────────────────────────────────
    records = load_reference_data(args.csv_dir)
    if not records:
        print("[main] ERROR: no reference data loaded — check --csv_dir path")
        sys.exit(1)

    # ── Run selector ─────────────────────────────────────────────────────
    top_k_results, all_results, conf_info = select_top_k(
        qM         = args.M,
        qK         = args.K,
        qN         = args.N,
        records    = records,
        top_k      = args.top_k,
        w_perf     = w_perf,
        w_resource = w_resource,
    )

    # ── Markdown report (auto-saved) ──────────────────────────────────────
    md_text = generate_markdown_report(
        args.M, args.K, args.N,
        top_k_results, all_results,
        w_perf=w_perf, w_resource=w_resource,
        conf_info=conf_info,
    )
    md_path = out_dir / f"report_{stem}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # ── Plain-text report (terminal + auto-saved) ─────────────────────────
    txt_text = generate_text_report(
        args.M, args.K, args.N,
        top_k_results, all_results,
        conf_info=conf_info,
    )
    print(txt_text)

    txt_path = out_dir / f"report_{stem}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_text)

    print(f"\n[main] Reports saved:")
    print(f"       Markdown → {md_path}")
    print(f"       Text     → {txt_path}")

    # ── Plot ──────────────────────────────────────────────────────────────
    if not args.no_plot:
        plot_path = str(out_dir / f"plot_{stem}.png")
        plot_tradeoff(
            all_results,
            top_k_results,
            save_path=plot_path,
        )
        print(f"       Plot     → {plot_path}")

    # ── RTL Generator ─────────────────────────────────────────────────────
    if not args.no_generate:
        rtl_dir = Path(args.rtl_dir)
        if not rtl_dir.is_dir():
            print(f"\n[main] ERROR: RTL source directory not found: {rtl_dir}")
            print(f"       Pass the correct path with --rtl_dir")
        else:
            print(f"\n[main] Generating RTL for top-{args.top_k} configurations...")
            generated_dirs = generate_rtl(
                top_k_results = top_k_results,
                rtl_src_dir   = rtl_dir,
                out_dir       = out_dir,
                qM            = args.M,
                qK            = args.K,
                qN            = args.N,
            )
            print(f"\n[main] RTL generated ({len(generated_dirs)} folder(s)):")
            for d in generated_dirs:
                print(f"       {d}")


if __name__ == "__main__":
    main()
