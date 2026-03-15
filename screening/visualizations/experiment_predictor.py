#!/usr/bin/env python3
"""
Experimental Outcome Predictor: predicted Cu wt% for Fontana Lab scenarios.

For a grid of realistic experiment conditions (oxide × dose × particle size),
predicts the final Cu concentration after 30 min at 1823K. Presented as a
heatmap table — green cells meet the 0.10 wt% target, red cells don't.

This is the "recipe card" for experiment planning: pick your oxide, read
across to find which dose + particle size combinations are predicted to work.

All predictions use DICTRA per-particle Cu capture (real kinetic data) with
stoichiometric capping. No empirical fudge factors.

Outputs: figures/experiment_predictor.png, .pdf
Run: python3 screening/visualizations/experiment_predictor.py
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
FIG_DIR = SCRIPT_DIR.parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
SUMMARY_CSV = RAW_DIR / "cu_removal_rate_summary.csv"

# ── Physical constants ─────────────────────────────────────────────
STEEL_MASS_KG = 0.50
CU_INIT_WT = 0.30   # wt%
TOTAL_CU_MG = STEEL_MASS_KG * 1e3 * CU_INIT_WT / 100 * 1e3  # 1500 mg
MW_CU = 63.546
CU_TARGET_WT = 0.10  # hot shortness threshold
TARGET_REMOVAL_PCT = (CU_INIT_WT - CU_TARGET_WT) / CU_INIT_WT * 100  # 66.7%
T_K = 1823
TIME_S = 1800  # 30 min

# ── Oxides ─────────────────────────────────────────────────────────
OXIDES = [
    ("Fe₂O₃",  5240, 1.0, 159.69, -111.9),
    ("V₂O₅",   3357, 3.0, 181.88, -109.2),
    ("MnO",    5430, 0.5,  70.94,  -63.5),
    ("SiO₂",   2650, 2.0,  60.08,  -50.2),
    ("Al₂O₃",  3950, 1.0, 101.96,  -35.7),
]

# ── Experiment grid ────────────────────────────────────────────────
DOSES = [1, 2, 3, 5, 10]        # grams
RADII = [50, 100, 250, 500]      # μm


# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════

def load_captures():
    """Load per-particle Cu capture for each radius at T=1823K, t=1800s."""
    caps = {}
    with open(SUMMARY_CSV) as f:
        for row in csv.DictReader(f):
            T = float(row["temp_K"])
            R = float(row["radius_um"])
            t = float(row["time_s"])
            if abs(T - T_K) < 1 and abs(t - TIME_S) < 1:
                caps[int(R)] = float(row["cu_captured_mg"])
    return caps


def predict_final_cu(cap, R_um, dose, rho, cu_per_mol, mw_oxide):
    """Predict final Cu wt% after experiment."""
    r_m = R_um * 1e-6
    v = (4 / 3) * math.pi * r_m ** 3
    m_p = rho * v * 1e3
    n = dose / m_p
    kin = cap * n
    stoich = (dose / mw_oxide) * cu_per_mol * MW_CU * 1e3
    captured = min(kin, stoich, TOTAL_CU_MG)
    remaining_mg = TOTAL_CU_MG - captured
    remaining_wt = remaining_mg / (STEEL_MASS_KG * 1e3 * 1e3) * 100
    return max(remaining_wt, 0.0)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    caps = load_captures()

    n_oxides = len(OXIDES)
    n_doses = len(DOSES)
    n_radii = len(RADII)

    fig, axes = plt.subplots(1, n_oxides, figsize=(18, 5.5),
                              sharey=True)

    # Custom colormap: red (high Cu = bad) → yellow → green (low Cu = good)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "cu_pred", ["#16a34a", "#a3e635", "#facc15", "#f97316", "#dc2626"],
        N=256,
    )

    for idx, (name, rho, cu_per_mol, mw, dG) in enumerate(OXIDES):
        ax = axes[idx]

        # Build prediction grid: rows=radius (top=small), cols=dose
        grid = np.zeros((n_radii, n_doses))
        for i, R in enumerate(RADII):
            cap = caps.get(R, caps[min(caps.keys(), key=lambda x: abs(x - R))])
            for j, dose in enumerate(DOSES):
                grid[i, j] = predict_final_cu(cap, R, dose, rho, cu_per_mol, mw)

        # Plot heatmap
        im = ax.imshow(grid, cmap=cmap, aspect="auto",
                       vmin=0, vmax=0.30, interpolation="nearest")

        # Cell text annotations
        for i in range(n_radii):
            for j in range(n_doses):
                val = grid[i, j]
                # Bold green text if meets target, else dark
                if val <= CU_TARGET_WT:
                    txt_color = "white"
                    weight = "bold"
                    txt = f"{val:.2f}"
                else:
                    txt_color = "black" if val < 0.20 else "white"
                    weight = "normal"
                    txt = f"{val:.2f}"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=9, color=txt_color, fontweight=weight)

        # Axis labels
        ax.set_xticks(range(n_doses))
        ax.set_xticklabels([f"{d}g" for d in DOSES], fontsize=9)
        ax.set_xlabel("Oxide dose", fontsize=10)

        if idx == 0:
            ax.set_yticks(range(n_radii))
            ax.set_yticklabels([f"{r} μm" for r in RADII], fontsize=9)
            ax.set_ylabel("Particle radius", fontsize=11)
        else:
            ax.set_yticks(range(n_radii))
            ax.set_yticklabels([])

        # Title with oxide name and dG
        ax.set_title(f"{name}\nΔG = {dG:.0f} kJ",
                     fontsize=11, fontweight="bold", pad=8)

        # Border around cells that meet target
        for i in range(n_radii):
            for j in range(n_doses):
                if grid[i, j] <= CU_TARGET_WT:
                    rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                         linewidth=2, edgecolor="white",
                                         facecolor="none", zorder=3)
                    ax.add_patch(rect)

    # Colorbar
    cbar = fig.colorbar(im, ax=axes, label="Predicted final Cu (wt%)",
                         pad=0.02, shrink=0.85)
    cbar.set_ticks([0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    # Mark target on colorbar
    cbar.ax.axhline(CU_TARGET_WT, color="white", linewidth=2, linestyle="--")
    cbar.ax.text(1.8, CU_TARGET_WT, "← 0.10% target",
                 transform=cbar.ax.get_yaxis_transform(),
                 fontsize=8, va="center", color="#333333")

    fig.suptitle(
        "Experiment Outcome Predictor: Predicted Final Cu wt%\n"
        f"T = {T_K} K,  t = 30 min,  {STEEL_MASS_KG} kg steel,  "
        f"{CU_INIT_WT} wt% Cu initial     "
        f"Green ≤ {CU_TARGET_WT} wt% (target)  |  Red > {CU_INIT_WT - 0.05} wt% (little removal)",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0, 0.92, 0.88])

    # Print summary
    print(f"Experiment predictor: T={T_K}K, t=30min, {STEEL_MASS_KG}kg steel, "
          f"{CU_INIT_WT}wt% Cu")
    print(f"Target: ≤ {CU_TARGET_WT} wt% Cu ({TARGET_REMOVAL_PCT:.1f}% removal)")
    print()
    for name, rho, cu_per_mol, mw, dG in OXIDES:
        feasible = []
        for R in RADII:
            cap = caps.get(R, caps[min(caps.keys(), key=lambda x: abs(x - R))])
            for dose in DOSES:
                val = predict_final_cu(cap, R, dose, rho, cu_per_mol, mw)
                if val <= CU_TARGET_WT:
                    feasible.append(f"R={R}/d={dose}g")
        n_feas = len(feasible)
        print(f"  {name:6s} (ΔG={dG:>6.1f}): {n_feas}/{n_doses * n_radii} "
              f"feasible combos" +
              (f" — min: {feasible[0]}" if feasible else ""))

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"experiment_predictor.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"\nSaved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
