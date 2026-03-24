from __future__ import annotations

import os
from pathlib import Path

from cocotb_tools.runner import get_runner


def _parse_defines(raw: str) -> dict[str, int]:
    defines: dict[str, int] = {}
    for token in raw.replace(",", " ").split():
        if "=" in token:
            key, value = token.split("=", 1)
            defines[key] = int(value, 0)
        else:
            defines[token] = 1
    return defines


def main() -> None:
    sim_dir = Path(__file__).resolve().parent
    rtl_dir = (sim_dir / ".." / "rtl").resolve()

    toplevel = os.environ.get("TOPLEVEL", "matrix_top_wrapper")
    module = os.environ.get("MODULE", "matrix_axi_wrapper_tb")
    sim = os.environ.get("SIM", "icarus")
    sim_build = sim_dir / os.environ.get("SIM_BUILD", f"sim_build_{toplevel}")
    results_xml = sim_dir / os.environ.get("RESULTS_XML", "matrix_wrapper_results.xml")
    defines = _parse_defines(os.environ.get("DEFINES", ""))

    sources = sorted(str(path) for path in rtl_dir.rglob("*.sv"))
    sources += sorted(str(path) for path in rtl_dir.rglob("*.v"))

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=toplevel,
        build_dir=str(sim_build),
        always=True,
        build_args=["-g2012"],
        defines=defines,
    )
    runner.test(
        hdl_toplevel=toplevel,
        test_module=module,
        test_dir=str(sim_dir),
        results_xml=str(results_xml),
    )


if __name__ == "__main__":
    main()
