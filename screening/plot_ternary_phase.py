"""
Plot ternary composition diagrams colored by stable phase at 1800K.

Reads ternary_phase_map_1800K.csv and produces ternary scatter plots
for each Cu-M-O system, colored by dominant equilibrium phase.

Uses matplotlib ternary projection (simplex coordinates).

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "ternary_phase_map_1800K.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

# Phase colors (assign most common phases distinct colors)
PHASE_COLORS = {
    "IONIC_LIQ": "#0077BB",       # blue
    "IONIC_LIQ#1": "#0077BB",
    "LIQUID": "#0077BB",
    "SPINEL": "#EE7733",          # orange
    "SPINEL#1": "#EE7733",
    "FCC_A1": "#AA3377",          # purple
    "FCC_A1#1": "#AA3377",
    "CORUNDUM": "#009988",        # teal
    "CORUNDUM#1": "#009988",
    "HALITE": "#BBBBBB",          # gray
    "HALITE#1": "#BBBBBB",
    "CU2O": "#EE3377",            # magenta
    "CUPRITE": "#EE3377",
}
DEFAULT_COLOR = "#444444"


def ternary_to_cartesian(x_cu, x_m, x_o):
    """Convert ternary coordinates to 2D Cartesian for equilateral triangle.

    Cu at bottom-left, M at bottom-right, O at top.
    """
    x = x_m + 0.5 * x_o
    y = x_o * (3**0.5 / 2)
    return x, y


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run ternary_phase_map_1800K.py on OSU VM first.")
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
            systems[sys_name] = []
        systems[sys_name].append(r)

    for sys_name, sys_rows in systems.items():
        print(f"\n{'='*60}")
        print(f"System: {sys_name} at 1800K")
        print(f"{'='*60}")

        # Parse compositions and phases
        x_cu_list = []
        x_m_list = []
        x_o_list = []
        dominant_list = []
        all_phases_set = set()

        for r in sys_rows:
            try:
                x_cu = float(r["X_Cu"])
                x_m = float(r["X_M"])
                x_o = float(r["X_O"])
                dominant = r.get("dominant_phase", "")
                if not dominant or "ERROR" in r.get("stable_phases", ""):
                    continue
                x_cu_list.append(x_cu)
                x_m_list.append(x_m)
                x_o_list.append(x_o)
                dominant_list.append(dominant)
                all_phases_set.add(dominant)
            except (ValueError, KeyError):
                pass

        if not x_cu_list:
            print("  No valid data points.")
            continue

        x_cu_arr = np.array(x_cu_list)
        x_m_arr = np.array(x_m_list)
        x_o_arr = np.array(x_o_list)

        # Convert to Cartesian
        x_cart, y_cart = ternary_to_cartesian(x_cu_arr, x_m_arr, x_o_arr)

        # Assign colors
        colors = [PHASE_COLORS.get(p, DEFAULT_COLOR) for p in dominant_list]

        # Phase frequency
        phase_counts = {}
        for p in dominant_list:
            phase_counts[p] = phase_counts.get(p, 0) + 1
        for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
            pct = 100.0 * count / len(dominant_list)
            print(f"  {phase:<20} {count:>4} ({pct:.0f}%)")

        # Plot
        fig, ax = plt.subplots(figsize=(8, 7))

        # Draw triangle outline
        tri_x = [0, 1, 0.5, 0]
        tri_y = [0, 0, 3**0.5/2, 0]
        ax.plot(tri_x, tri_y, 'k-', linewidth=1.0)

        # Scatter points colored by dominant phase
        # Group by phase for legend
        plotted_phases = set()
        for phase in sorted(all_phases_set):
            mask = [p == phase for p in dominant_list]
            if not any(mask):
                continue
            x_pts = x_cart[np.array(mask)]
            y_pts = y_cart[np.array(mask)]
            color = PHASE_COLORS.get(phase, DEFAULT_COLOR)
            ax.scatter(x_pts, y_pts, c=color, s=40, label=phase,
                       edgecolors='black', linewidths=0.3, alpha=0.8)
            plotted_phases.add(phase)

        # Vertex labels
        metal = sys_name.split("-")[1]  # e.g., "Al" from "Cu-Al-O"
        ax.text(0, -0.04, "Cu", ha='center', va='top', fontsize=12, fontweight='bold')
        ax.text(1, -0.04, metal, ha='center', va='top', fontsize=12, fontweight='bold')
        ax.text(0.5, 3**0.5/2 + 0.03, "O", ha='center', va='bottom',
                fontsize=12, fontweight='bold')

        ax.set_xlim(-0.08, 1.08)
        ax.set_ylim(-0.1, 3**0.5/2 + 0.1)
        ax.set_aspect('equal')
        ax.axis('off')

        ax.set_title(f"{sys_name} Phase Map at 1800 K", fontsize=13, pad=20)
        ax.legend(loc='upper right', fontsize=9, framealpha=0.9,
                  bbox_to_anchor=(1.15, 1.0))

        plt.tight_layout()

        # Save
        safe_name = sys_name.replace("-", "_").lower()
        png_path = FIG_DIR / f"phase_map_{safe_name}_1800K.png"
        pdf_path = FIG_DIR / f"phase_map_{safe_name}_1800K.pdf"
        fig.savefig(png_path, dpi=300, bbox_inches='tight')
        fig.savefig(pdf_path, bbox_inches='tight')
        plt.close(fig)

        print(f"  Saved: {png_path}")
        print(f"  Saved: {pdf_path}")


if __name__ == "__main__":
    main()
