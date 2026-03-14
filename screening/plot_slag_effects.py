"""
Plot Cu activity vs slag basicity ratio.

Reads slag_composition_effects.csv and produces a figure showing
a_Cu vs basicity ratio (MnO:SiO2 or Al2O3:SiO2) at 1800K.

If a_Cu decreases with increasing basicity, basic slag promotes
Cu capture (lower Cu activity = more Cu dissolved in slag).

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "slag_composition_effects.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

COLORS = {
    "Cu-Mn-Si-O": "#0077BB",   # blue
    "Cu-Al-Si-O": "#EE7733",   # orange
}

LINE_STYLES = {
    "Cu-Mn-Si-O": "-",
    "Cu-Al-Si-O": "--",
}

MARKERS = {
    "Cu-Mn-Si-O": "o",
    "Cu-Al-Si-O": "s",
}


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run slag_composition_effects.py on OSU VM first.")
        return

    FIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(CSV_IN) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by system
    systems = {}
    for r in rows:
        sys_name = r["system"]
        if sys_name not in systems:
            systems[sys_name] = {
                "ratio": [], "a_Cu": [], "ratio_label": r["ratio_label"],
            }
        try:
            ratio = float(r["ratio_value"])
            a_Cu = float(r["a_Cu"])
            systems[sys_name]["ratio"].append(ratio)
            systems[sys_name]["a_Cu"].append(a_Cu)
        except (ValueError, KeyError):
            pass

    if not systems:
        print("ERROR: No valid data found.")
        return

    # Plot
    fig, ax = plt.subplots(figsize=(9, 5.5))

    line_ends = {}
    for sys_name in ["Cu-Mn-Si-O", "Cu-Al-Si-O"]:
        if sys_name not in systems:
            continue
        data = systems[sys_name]
        ratio = np.array(data["ratio"])
        a_Cu = np.array(data["a_Cu"])

        order = np.argsort(ratio)
        ratio = ratio[order]
        a_Cu = a_Cu[order]

        ax.plot(ratio, a_Cu,
                color=COLORS.get(sys_name, "#333333"),
                linestyle=LINE_STYLES.get(sys_name, "-"),
                marker=MARKERS.get(sys_name, "o"),
                markersize=6,
                linewidth=1.8)

        # Store for inline labels
        line_ends[sys_name] = (ratio[-1], a_Cu[-1], data['ratio_label'])

    ax.set_xlabel("Basicity ratio (basic oxide : SiO$_2$)", fontsize=12)
    ax.set_ylabel("Cu activity (a$_{Cu}$)", fontsize=12)
    ax.set_title("Effect of Slag Basicity on Cu Activity at 1800 K\n"
                 "(X$_{Cu}$ = 0.003, steelmaking level)", fontsize=12)

    # Gridlines per CLAUDE.md
    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)

    # Remove outer box
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Inline labels at right end of each line
    for sys_name, (x_end, y_end, ratio_label) in line_ends.items():
        label_text = f"{sys_name}\n({ratio_label})"
        ax.annotate(
            label_text,
            xy=(x_end, y_end),
            xytext=(8, 0),
            textcoords='offset points',
            fontsize=8.5,
            fontweight='bold',
            color=COLORS.get(sys_name, "#333333"),
            ha='left',
            va='center',
        )

    plt.tight_layout()

    png_path = FIG_DIR / "slag_basicity_vs_aCu.png"
    pdf_path = FIG_DIR / "slag_basicity_vs_aCu.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)

    print(f"Figures saved:")
    print(f"  {png_path}")
    print(f"  {pdf_path}")

    # Summary
    print(f"\n{'System':<16} {'a_Cu(low R)':>12} {'a_Cu(high R)':>14} {'Trend':>12}")
    print("-" * 58)
    for sys_name, data in systems.items():
        if len(data["a_Cu"]) < 2:
            continue
        ratio = np.array(data["ratio"])
        a_Cu = np.array(data["a_Cu"])
        order = np.argsort(ratio)
        a_low = a_Cu[order[0]]
        a_high = a_Cu[order[-1]]
        if a_high < a_low:
            trend = "decreasing"
        elif a_high > a_low:
            trend = "increasing"
        else:
            trend = "flat"
        print(f"{sys_name:<16} {a_low:>12.6f} {a_high:>14.6f} {trend:>12}")


if __name__ == "__main__":
    main()
