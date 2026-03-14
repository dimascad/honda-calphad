"""
Plot Cu activity vs oxide fraction for 4 systems at 1800K.

Reads cu_activity_vs_oxide.csv and produces a publication-quality figure
showing how Cu activity drops as oxide is dissolved into the Cu melt.
Steeper drop = stronger Cu-oxide interaction.

Colorblind-friendly palette per CLAUDE.md:
  Blue: #0077BB, Orange: #EE7733, Purple: #AA3377, + Teal: #009988

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "cu_activity_vs_oxide.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

# Colorblind-friendly palette (CLAUDE.md)
COLORS = {
    "Cu-Al-O": "#0077BB",
    "Cu-Mn-O": "#EE7733",
    "Cu-Fe-O": "#AA3377",
    "Cu-V-O":  "#009988",
}

LINE_STYLES = {
    "Cu-Al-O": "-",
    "Cu-Mn-O": "--",
    "Cu-Fe-O": ":",
    "Cu-V-O":  "-.",
}

MARKERS = {
    "Cu-Al-O": "o",
    "Cu-Mn-O": "s",
    "Cu-Fe-O": "^",
    "Cu-V-O":  "D",
}


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run cu_activity_vs_oxide.py on OSU VM first.")
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
            systems[sys_name] = {"X_Cu": [], "a_Cu": [], "oxide": r["oxide"]}
        try:
            X_Cu = float(r["X_Cu"])
            a_Cu = float(r["a_Cu"])
            systems[sys_name]["X_Cu"].append(X_Cu)
            systems[sys_name]["a_Cu"].append(a_Cu)
        except (ValueError, KeyError):
            pass

    if not systems:
        print("ERROR: No valid data found.")
        return

    # Plot
    fig, ax = plt.subplots(figsize=(9, 5.5))

    line_data = {}
    for sys_name in ["Cu-Al-O", "Cu-Mn-O", "Cu-Fe-O", "Cu-V-O"]:
        if sys_name not in systems:
            continue
        data = systems[sys_name]
        X_Cu = np.array(data["X_Cu"])
        a_Cu = np.array(data["a_Cu"])

        # X-axis: oxide fraction = 1 - X_Cu
        X_oxide = 1 - X_Cu

        # Sort by X_oxide
        order = np.argsort(X_oxide)
        X_oxide = X_oxide[order]
        a_Cu = a_Cu[order]

        ax.plot(X_oxide, a_Cu,
                color=COLORS[sys_name],
                linestyle=LINE_STYLES[sys_name],
                marker=MARKERS[sys_name],
                markersize=5,
                linewidth=1.8)

        line_data[sys_name] = (X_oxide, a_Cu, data['oxide'])

    ax.set_xlabel("Oxide mole fraction (1 - X$_{Cu}$)", fontsize=12)
    ax.set_ylabel("Cu activity (a$_{Cu}$)", fontsize=12)
    ax.set_title("Cu Activity vs. Oxide Addition at 1800 K", fontsize=13)

    ax.set_xlim(0, 1.05)
    ax.set_ylim(bottom=0)

    # Gridlines per CLAUDE.md
    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)

    # Remove outer box
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(which='both', direction='in')

    # Inline labels — place at the left side (~X_oxide = 0.15) where lines
    # are most separated, with y-offsets to avoid overlap
    LABEL_CONFIG = {
        "Cu-Al-O":  (0.15, 10),   # (x_pos_idx, y_offset_pts)
        "Cu-Mn-O":  (0.15, -14),
        "Cu-Fe-O":  (0.35, -12),
        "Cu-V-O":   (0.15, -14),
    }
    for sys_name, (x_target, y_off) in LABEL_CONFIG.items():
        if sys_name not in line_data:
            continue
        X_oxide, a_Cu, oxide = line_data[sys_name]
        idx = int(np.argmin(np.abs(X_oxide - x_target)))
        label_text = f"{sys_name} ({oxide})"
        ax.annotate(
            label_text,
            xy=(X_oxide[idx], a_Cu[idx]),
            xytext=(0, y_off),
            textcoords='offset points',
            fontsize=8.5,
            fontweight='bold',
            color=COLORS[sys_name],
            ha='center',
            va='center',
        )

    plt.tight_layout()

    # Save
    png_path = FIG_DIR / "cu_activity_vs_oxide.png"
    pdf_path = FIG_DIR / "cu_activity_vs_oxide.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)

    print(f"Figures saved:")
    print(f"  {png_path}")
    print(f"  {pdf_path}")

    # Print summary
    print(f"\n{'System':<12} {'a_Cu @ X_ox=0.1':>16} {'a_Cu @ X_ox=0.5':>16} {'a_Cu @ X_ox=0.9':>16}")
    print("-" * 64)
    for sys_name in ["Cu-Al-O", "Cu-Mn-O", "Cu-Fe-O", "Cu-V-O"]:
        if sys_name not in systems:
            continue
        data = systems[sys_name]
        X_Cu = np.array(data["X_Cu"])
        a_Cu = np.array(data["a_Cu"])
        line = f"{sys_name:<12}"
        for x_target in [0.1, 0.5, 0.9]:
            X_ox = 1 - X_Cu
            idx = int(np.argmin(np.abs(X_ox - x_target)))
            if np.abs(X_ox[idx] - x_target) < 0.1:
                line += f" {a_Cu[idx]:>16.4f}"
            else:
                line += f" {'N/A':>16}"
        print(line)


if __name__ == "__main__":
    main()
