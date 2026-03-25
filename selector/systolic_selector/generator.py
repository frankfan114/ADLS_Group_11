"""
generator.py
------------
RTL generator for the systolic array selector.

After the selector picks the top-K (variant, dim) configurations, this module:
  1. Copies the matching RTL source folder for each candidate.
  2. Patches MAX_M / MAX_K / MAX_N in matrix_top_wrapper.v to the selected dim.
  3. Writes a selector_config.txt manifest with the selection metadata.

Output layout (inside --out_dir / generated_rtl/):
  rank1_WS_dim16/
    matrix_top_wrapper.v    ← patched parameters
    matrix_pe.sv
    ...
    selector_config.txt     ← selection metadata
  rank2_OS_PP_dim8/
    ...
"""

import re
import shutil
from pathlib import Path

# Maps selector variant keys → RTL subfolder names
VARIANT_TO_RTL_DIR = {
    "OS":     "output_stationary",
    "WS":     "weight_stationary",
    "OS_PP":  "os_pp",
    "WS_PP":  "ws_pp",
    "RSA_WS": "rsa_ws",
    "SMT_SA": "smt_sa",
}

# Verilog parameter lines to patch in matrix_top_wrapper.v
_PARAM_PATTERN = re.compile(
    r"(parameter\s+MAX_([MKN])\s*=\s*)\d+(\s*[,;])",
    re.IGNORECASE,
)


def _patch_wrapper(src_text: str, dim: int) -> str:
    """Replace MAX_M / MAX_K / MAX_N parameter defaults with *dim*."""
    def replacer(m):
        return f"{m.group(1)}{dim}{m.group(3)}"
    return _PARAM_PATTERN.sub(replacer, src_text)


def _write_manifest(dest_dir: Path, rank: int, candidate: dict,
                    qM: int, qK: int, qN: int) -> None:
    """Write a human-readable selector_config.txt inside the RTL output folder."""
    m = candidate.get("metrics", {})
    lines = [
        "=" * 56,
        f"  Selector RTL Config — Rank #{rank}",
        "=" * 56,
        f"  Query layer          : M={qM}  K={qK}  N={qN}",
        f"  Variant              : {candidate['variant']}",
        f"  Array dim (MAX_M/K/N): {candidate['dim']}",
        f"  Final score          : {candidate['score']:.4f}",
        f"  Perf  score          : {candidate['perf_score']:.4f}",
        f"  Resource score       : {candidate['resource_score']:.4f}",
        "-" * 56,
        "  Predicted performance metrics",
        f"    latency_cycles       : {m.get('latency_cycles', 'N/A')}",
        f"    throughput_mac/cycle : {m.get('throughput_mac_per_cycle', 'N/A'):.4f}",
        f"    memory_stall_ratio   : {m.get('memory_stall_ratio', 'N/A'):.4f}",
        f"    pe_utilization       : {m.get('pe_utilization', 'N/A'):.4f}",
        "-" * 56,
        "  Predicted resource metrics",
        f"    physical_pe_count    : {m.get('physical_pe_count', 'N/A')}",
        f"    read_bytes           : {m.get('read_bytes', 'N/A')}",
        f"    b_reads              : {m.get('b_reads', 'N/A')}",
        "=" * 56,
        "",
        "  RTL parameters patched in matrix_top_wrapper.v:",
        f"    MAX_M = {candidate['dim']}",
        f"    MAX_K = {candidate['dim']}",
        f"    MAX_N = {candidate['dim']}",
        "=" * 56,
    ]
    (dest_dir / "selector_config.txt").write_text("\n".join(lines), encoding="utf-8")


def generate_rtl(
    top_k_results: list,
    rtl_src_dir: str | Path,
    out_dir: str | Path,
    qM: int,
    qK: int,
    qN: int,
) -> list[Path]:
    """
    Generate patched RTL folders for each top-K candidate.

    Parameters
    ----------
    top_k_results : list[dict]
        Ordered list of candidate dicts returned by select_top_k().
    rtl_src_dir : str | Path
        Path to the root RTL folder (contains output_stationary/, weight_stationary/, …).
    out_dir : str | Path
        Root output directory. RTL folders are created under out_dir/generated_rtl/.
    qM, qK, qN : int
        Query layer dimensions (used only for the manifest text).

    Returns
    -------
    list[Path]
        Paths to the generated RTL folders (one per top-K candidate).
    """
    rtl_src_dir = Path(rtl_src_dir)
    gen_root    = Path(out_dir) / "generated_rtl"
    gen_root.mkdir(parents=True, exist_ok=True)

    generated = []

    for rank, candidate in enumerate(top_k_results, start=1):
        variant = candidate["variant"]
        dim     = candidate["dim"]

        rtl_subdir = VARIANT_TO_RTL_DIR.get(variant)
        if rtl_subdir is None:
            print(f"[generator] WARNING: unknown variant '{variant}' — skipping rank {rank}")
            continue

        src_folder = rtl_src_dir / rtl_subdir
        if not src_folder.is_dir():
            print(f"[generator] WARNING: RTL source not found at {src_folder} — skipping")
            continue

        # Destination folder name: rank1_WS_dim16
        dest_name   = f"rank{rank}_{variant}_dim{dim}"
        dest_folder = gen_root / dest_name

        # Copy entire RTL folder (overwrite if already exists)
        if dest_folder.exists():
            shutil.rmtree(dest_folder)
        shutil.copytree(src_folder, dest_folder)

        # Patch matrix_top_wrapper.v
        wrapper_path = dest_folder / "matrix_top_wrapper.v"
        if wrapper_path.exists():
            original = wrapper_path.read_text(encoding="utf-8")
            patched  = _patch_wrapper(original, dim)
            wrapper_path.write_text(patched, encoding="utf-8")
            print(f"[generator] Patched  MAX_M/K/N = {dim} in {wrapper_path.name}")
        else:
            print(f"[generator] WARNING: matrix_top_wrapper.v not found in {dest_folder}")

        # Write manifest
        _write_manifest(dest_folder, rank, candidate, qM, qK, qN)

        print(f"[generator] Rank #{rank}  {variant} dim={dim}  →  {dest_folder}")
        generated.append(dest_folder)

    return generated
