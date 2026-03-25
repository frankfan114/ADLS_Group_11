"""
Generate a resource comparison table image for 4x4 designs from resouces/resource.md
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


RESOURCE_FILE = "resouces/resource.md"

# Fields to extract from Slice Logic table
SLICE_FIELDS = [
    "Slice LUTs",
    "Slice Registers",
    "F7 Muxes",
    "F8 Muxes",
]

# Available counts for the device xc7a200tsbv484-1
AVAILABLE = {
    "Slice LUTs":      134600,
    "Slice Registers": 269200,
    "F7 Muxes":        67300,
    "F8 Muxes":        33650,
    "DSPs":            740,
}


def parse_resource_md(filepath):
    """Parse resource.md and return data for all 4x4 designs."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into sections by design header (e.g. "os 4*4:", "ws_pp 4*4:")
    # Header pattern: word chars (possibly with underscore) + space + digits*digits + colon
    section_pattern = re.compile(
        r'^([\w]+(?:_[\w]+)*\s+\d+[\\]?\*\d+)\s*:',
        re.MULTILINE
    )

    sections = {}
    matches = list(section_pattern.finditer(content))
    for i, m in enumerate(matches):
        name_raw = m.group(1).strip()
        # Normalize: remove backslash, normalize spaces
        name = re.sub(r'\\', '', name_raw).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[name] = content[start:end]

    # Filter to 4x4 only
    data = {}
    for name, text in sections.items():
        if "4*4" not in name and "4x4" not in name.lower():
            continue
        design_name = name.replace("4*4", "").replace("4x4", "").strip()
        if not design_name:
            design_name = "unknown"

        row = {}

        # Extract slice logic fields (Used column)
        for field in SLICE_FIELDS:
            # Match table row like "| Slice LUTs* | 4451 | ..."
            pattern = re.compile(
                r'\|\s*' + re.escape(field) + r'[\\]?\*?\s*\|\s*(\d+)\s*\|'
            )
            m = pattern.search(text)
            row[field] = int(m.group(1)) if m else 0

        # Extract DSP count
        dsp_pattern = re.compile(r'\|\s*DSPs\s*\|\s*(\d+)\s*\|')
        m = dsp_pattern.search(text)
        row["DSPs"] = int(m.group(1)) if m else 0

        data[design_name] = row

    return data


def build_table(data):
    """Build ordered list of rows and columns for the table."""
    # Desired display order for designs
    order = ["os", "ws", "os_pp", "ws_pp", "rsa_ws"]
    designs = []
    for key in order:
        if key in data:
            designs.append(key)
    # Append any extras not in order list
    for key in data:
        if key not in designs:
            designs.append(key)

    columns = SLICE_FIELDS + ["DSPs"]
    return designs, columns


def _prepare_data(data):
    """Compute cell_vals and cell_util for all designs/columns."""
    designs, columns = build_table(data)
    cell_vals, cell_util = [], []
    for d in designs:
        row_vals, row_util = [], []
        for col in columns:
            used = data[d].get(col, 0)
            pct = used / AVAILABLE.get(col, 1) * 100
            row_vals.append(used)
            row_util.append(pct)
        cell_vals.append(row_vals)
        cell_util.append(row_util)
    return designs, columns, cell_vals, cell_util


def render_table(data):
    designs, columns, cell_vals, cell_util = _prepare_data(data)
    n_rows, n_cols = len(designs), len(columns)

    fig_w = 2.2 + n_cols * 1.8
    fig_h = 1.0 + n_rows * 0.65
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    col_labels = [c.replace(" ", "\n") for c in columns]

    cell_text = []
    for ri in range(n_rows):
        row_text = []
        for ci in range(n_cols):
            used = cell_vals[ri][ci]
            pct = cell_util[ri][ci]
            row_text.append(f"{used:,}\n({pct:.2f}%)")
        cell_text.append(row_text)

    cell_colors = []
    for ri in range(n_rows):
        row_colors = []
        for ci in range(n_cols):
            pct = cell_util[ri][ci] / 100.0
            r = 1.0
            g = 1.0 - pct * 0.55
            b = 1.0 - pct * 0.65
            row_colors.append((r, g, b))
        cell_colors.append(row_colors)

    table = ax.table(
        cellText=cell_text,
        rowLabels=designs,
        colLabels=col_labels,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2.2)

    for (row, col), cell in table.get_celld().items():
        if row == 0 or col == -1:
            cell.set_facecolor("#2C3E50")
            cell.set_text_props(color="white", fontweight="bold")
        cell.set_edgecolor("#AAAAAA")

    ax.set_title(
        "FPGA Resource Utilization — 4×4 Designs\n(Device: xc7a200tsbv484-1)",
        fontsize=13, fontweight="bold", pad=10
    )

    plt.tight_layout(pad=1.2)
    out = "resource_4x4_table.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()


def render_chart(data, exclude=None, output="resource_4x4_chart.png"):
    designs, columns, cell_vals, cell_util = _prepare_data(data)
    if exclude:
        keep = [i for i, c in enumerate(columns) if c not in exclude]
        columns   = [columns[i]           for i in keep]
        cell_vals = [[r[i] for i in keep] for r in cell_vals]
        cell_util = [[r[i] for i in keep] for r in cell_util]
    n_rows, n_cols = len(designs), len(columns)

    fig, ax = plt.subplots(figsize=(2.2 + n_cols * 1.8, 4.5))
    x = np.arange(n_cols)
    width = 0.8 / n_rows
    colors = plt.cm.tab10(np.linspace(0, 0.6, n_rows))

    for ri, (design, color) in enumerate(zip(designs, colors)):
        offsets = x + (ri - n_rows / 2 + 0.5) * width
        vals = cell_util[ri]
        bars = ax.bar(offsets, vals, width * 0.9, label=design,
                      color=color, edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            if v > 1.5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    f"{v:.1f}%",
                    ha="center", va="bottom", fontsize=6.5, rotation=90
                )

    ax.set_xticks(x)
    ax.set_xticklabels(columns, fontsize=9)
    ax.set_ylabel("Utilization (%)", fontsize=9)
    ax.set_title("Resource Utilization Comparison — 4×4 Designs", fontsize=11, fontweight="bold")
    ax.legend(title="Design", fontsize=8, title_fontsize=8,
               loc="upper left", framealpha=0.85)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout(pad=1.2)
    out = output
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()


def main():
    data = parse_resource_md(RESOURCE_FILE)
    if not data:
        print("No 4x4 design data found.")
        return

    print(f"Found {len(data)} 4x4 design(s): {list(data.keys())}")
    for design, row in data.items():
        print(f"  {design}: {row}")

    render_table(data)
    render_chart(data)
    render_chart(data, exclude=["DSPs"], output="resource_4x4_chart_no_dsp.png")


if __name__ == "__main__":
    main()
