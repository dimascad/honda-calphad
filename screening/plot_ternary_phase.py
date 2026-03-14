"""
Plot ternary composition diagrams colored by stable phase at 1800K.

Reads ternary_phase_map_1800K.csv and produces filled ternary phase maps
for each Cu-M-O system, using Delaunay triangulation with tripcolor.

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "ternary_phase_map_1800K.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

# Phase colors — maximally distinct, designed for adjacency contrast
# Adjacent pairs checked: IONIC_LIQ#1/GAS, GAS/CORUNDUM, GAS/HALITE,
# IONIC_LIQ#1/IONIC_LIQ#2, IONIC_LIQ#1/HALITE, IONIC_LIQ#2/GAS
PHASE_COLORS = {
    "IONIC_LIQ#1": "#0077BB",     # blue (primary slag)
    "IONIC_LIQ#2": "#EE3377",     # magenta (immiscible second liquid)
    "GAS#1":       "#DDCC77",     # sand/yellow (gas)
    "CORUNDUM#1":  "#882255",     # dark wine (Al2O3 solid)
    "HALITE#1":    "#117733",     # dark green (MnO rock-salt)
}

# Display names for legend and labels
PHASE_DISPLAY = {
    "IONIC_LIQ#1": "Ionic Liquid (slag)",
    "IONIC_LIQ#2": "Ionic Liquid #2",
    "GAS#1":       "Gas (O$_2$-rich)",
    "CORUNDUM#1":  "Corundum (Al$_2$O$_3$)",
    "HALITE#1":    "Halite (MnO)",
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

        # Phase frequency
        phase_counts = {}
        for p in dominant_list:
            phase_counts[p] = phase_counts.get(p, 0) + 1
        for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
            pct = 100.0 * count / len(dominant_list)
            print(f"  {phase:<20} {count:>4} ({pct:.0f}%)")

        # Build phase index mapping for this system
        sorted_phases = sorted(all_phases_set)
        phase_to_idx = {p: i for i, p in enumerate(sorted_phases)}
        phase_indices = np.array([phase_to_idx[p] for p in dominant_list])

        # Build discrete colormap for this system's phases
        cmap_colors = [PHASE_COLORS.get(p, DEFAULT_COLOR) for p in sorted_phases]
        cmap = mcolors.ListedColormap(cmap_colors)
        norm = mcolors.BoundaryNorm(
            boundaries=np.arange(-0.5, len(sorted_phases), 1),
            ncolors=len(sorted_phases)
        )

        # Delaunay triangulation
        triang = mtri.Triangulation(x_cart, y_cart)

        # For each triangle, assign the majority phase of its 3 vertices
        tri_phase = np.zeros(len(triang.triangles), dtype=int)
        for i, tri in enumerate(triang.triangles):
            vertex_phases = phase_indices[tri]
            # Majority vote
            counts = np.bincount(vertex_phases, minlength=len(sorted_phases))
            tri_phase[i] = np.argmax(counts)

        # ---- Plot ----
        fig, ax = plt.subplots(figsize=(8, 7.5))
        h = 3**0.5 / 2  # height of equilateral triangle

        # Filled triangulation
        ax.tripcolor(triang, tri_phase, cmap=cmap, norm=norm,
                     edgecolors='none', alpha=0.85)

        # Draw phase boundaries: edges where adjacent triangles differ
        # Build triangle adjacency
        from matplotlib.tri import TriAnalyzer
        # Manual boundary detection
        edge_to_tris = {}
        for ti, tri in enumerate(triang.triangles):
            for e in [(tri[0], tri[1]), (tri[1], tri[2]), (tri[0], tri[2])]:
                edge = tuple(sorted(e))
                if edge not in edge_to_tris:
                    edge_to_tris[edge] = []
                edge_to_tris[edge].append(ti)

        for edge, tris in edge_to_tris.items():
            if len(tris) == 2 and tri_phase[tris[0]] != tri_phase[tris[1]]:
                p0, p1 = edge
                ax.plot([x_cart[p0], x_cart[p1]], [y_cart[p0], y_cart[p1]],
                        'k-', linewidth=1.0, alpha=0.6)

        # Draw triangle outline (on top)
        tri_x = [0, 1, 0.5, 0]
        tri_y = [0, 0, h, 0]
        ax.plot(tri_x, tri_y, 'k-', linewidth=1.5)

        # Tick marks and percentage labels on ALL 3 edges
        metal = sys_name.split("-")[1]  # e.g., "Al" from "Cu-Al-O"
        for frac in [0.2, 0.4, 0.6, 0.8]:
            tick_len = 0.015
            pct_str = f"{int(frac*100)}%"

            # Bottom edge: Cu (left) to Metal (right) — X_M increases
            bx, by = frac, 0
            ax.plot([bx, bx], [by - tick_len, by + tick_len], 'k-', lw=0.6)
            ax.text(bx, -0.035, pct_str, ha='center', va='top',
                    fontsize=7, color='#666666')

            # Left edge: Cu (bottom) to O (top) — X_O increases going up
            lx = 0.5 * frac
            ly = h * frac
            # Perpendicular outward (to the left)
            dx_l = -tick_len * np.cos(np.pi/6)
            dy_l = -tick_len * np.sin(np.pi/6)
            ax.plot([lx, lx + dx_l], [ly, ly + dy_l], 'k-', lw=0.6)
            ax.text(lx + dx_l * 2.5, ly + dy_l * 2.5, pct_str,
                    ha='center', va='center', fontsize=7, color='#666666',
                    rotation=60)

            # Right edge: Metal (bottom) to O (top) — X_O increases going up
            rx = 1 - 0.5 * frac
            ry = h * frac
            dx_r = tick_len * np.cos(np.pi/6)
            dy_r = -tick_len * np.sin(np.pi/6)
            ax.plot([rx, rx + dx_r], [ry, ry + dy_r], 'k-', lw=0.6)
            ax.text(rx + dx_r * 2.5, ry + dy_r * 2.5, pct_str,
                    ha='center', va='center', fontsize=7, color='#666666',
                    rotation=-60)

        # Vertex labels
        ax.text(0, -0.06, "Cu", ha='center', va='top', fontsize=13, fontweight='bold')
        ax.text(1, -0.06, metal, ha='center', va='top', fontsize=13, fontweight='bold')
        ax.text(0.5, h + 0.04, "O", ha='center', va='bottom',
                fontsize=13, fontweight='bold')

        # Edge labels
        ax.text(0.5, -0.075, r"X$_{" + metal + r"}$ $\rightarrow$",
                ha='center', va='top', fontsize=8, color='#888888')
        # Left edge label
        ax.text(0.14, h * 0.5 + 0.02, r"$\leftarrow$ X$_{O}$",
                ha='center', va='center', fontsize=8, color='#888888',
                rotation=60)
        # Right edge label
        ax.text(0.86, h * 0.5 + 0.02, r"X$_{O}$ $\rightarrow$",
                ha='center', va='center', fontsize=8, color='#888888',
                rotation=-60)

        # In-plot region labels at centroid of each phase cluster
        for phase in sorted(all_phases_set):
            mask = np.array([p == phase for p in dominant_list])
            if not any(mask):
                continue
            x_pts = x_cart[mask]
            y_pts = y_cart[mask]
            cx, cy = np.mean(x_pts), np.mean(y_pts)
            count = np.sum(mask)
            pct = 100.0 * count / len(dominant_list)

            color = PHASE_COLORS.get(phase, DEFAULT_COLOR)
            display_name = PHASE_DISPLAY.get(phase, phase.replace("#1", "").replace("_", " "))
            # Use short name for in-plot label
            short_name = phase.replace("#1", "").replace("#2", " #2").replace("_", " ")

            # Always label (no minimum threshold)
            ax.text(cx, cy, f"{short_name}\n({pct:.0f}%)",
                    ha='center', va='center', fontsize=7.5, fontweight='bold',
                    color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=color,
                              edgecolor='white', linewidth=0.5, alpha=0.9))

        # Legend
        legend_patches = []
        for phase in sorted_phases:
            color = PHASE_COLORS.get(phase, DEFAULT_COLOR)
            display = PHASE_DISPLAY.get(phase, phase)
            count = phase_counts.get(phase, 0)
            pct = 100.0 * count / len(dominant_list)
            legend_patches.append(
                mpatches.Patch(facecolor=color, edgecolor='black', linewidth=0.5,
                               label=f"{display} ({pct:.0f}%)")
            )
        ax.legend(handles=legend_patches, loc='upper right',
                  fontsize=7, framealpha=0.9, edgecolor='#CCCCCC',
                  bbox_to_anchor=(1.12, 1.0))

        ax.set_xlim(-0.15, 1.18)
        ax.set_ylim(-0.12, h + 0.1)
        ax.set_aspect('equal')
        ax.axis('off')

        ax.set_title(f"{sys_name} Phase Map at 1800 K", fontsize=13, pad=20)

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
