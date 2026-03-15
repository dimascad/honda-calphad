#!/usr/bin/env python3
"""
Dose-Response Curves: Cu removal % vs oxide dose for 5 candidate oxides.

Answers the key experiment design question: "How many grams do I need?"

Two panels compare:
  - Left (30 min): stoichiometry-limited regime. Cu diffuses fast enough
    that the oxide's molar Cu capacity (cu_per_mol / MW) is the bottleneck.
  - Right (1 min): kinetics-limited regime. Per-particle Cu capture is small,
    so you need many more particles (= more grams) to reach the same removal.

The contrast reveals which parameter matters most at a given contact time.

DICTRA kinetics are oxide-independent: per-particle Cu capture is the same
for all 5 oxides (same liquid Fe diffusion). What differs is density
(particle count per gram) and stoichiometric capacity (Cu atoms per mol oxide).

Outputs: figures/dose_response_curves.png, .pdf
Run: python3 screening/visualizations/dose_response_curves.py
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
FIG_DIR = SCRIPT_DIR.parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
SUMMARY_CSV = RAW_DIR / "cu_removal_rate_summary.csv"

# ── Physical constants ─────────────────────────────────────────────
STEEL_MASS_KG = 0.50
CU_INIT_WT = 0.30        # wt%
TOTAL_CU_MG = STEEL_MASS_KG * 1e3 * CU_INIT_WT / 100 * 1e3  # 1500 mg
MW_CU = 63.546            # g/mol
TARGET_PCT = 66.7          # removal target (0.30 → 0.10 wt%)
R_UM = 100                 # particle radius, μm
T_K = 1823                 # temperature, K

# ── Oxide database ─────────────────────────────────────────────────
# (name, formula, density kg/m³, cu_per_mol, MW g/mol, color, marker)
OXIDES = [
    ("Fe₂O₃",  5240, 1.0, 159.69, "#0077BB", "o"),
    ("V₂O₅",   3357, 3.0, 181.88, "#EE7733", "s"),
    ("MnO",    5430, 0.5,  70.94, "#AA3377", "^"),
    ("SiO₂",   2650, 2.0,  60.08, "#009988", "D"),
    ("Al₂O₃",  3950, 1.0, 101.96, "#CC3311", "v"),
]

# ── Dose sweep ─────────────────────────────────────────────────────
DOSES = np.linspace(0.05, 20, 500)


# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════

def load_dictra_capture(time_s):
    """Load per-particle Cu capture (mg) at T=1823K, R=100μm for given time."""
    with open(SUMMARY_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (abs(float(row["temp_K"]) - T_K) < 1
                    and abs(float(row["radius_um"]) - R_UM) < 1
                    and abs(float(row["time_s"]) - time_s) < 1):
                return float(row["cu_captured_mg"])
    raise ValueError(f"No DICTRA data for T={T_K}, R={R_UM}, t={time_s}")


def compute_removal_curve(doses, rho, cu_per_mol, mw_oxide, cu_captured_mg):
    """Compute removal % for a dose array, capping at stoich and total Cu."""
    r_m = R_UM * 1e-6
    v_particle = (4 / 3) * math.pi * r_m ** 3
    m_particle_g = rho * v_particle * 1e3  # kg → g

    removals = np.empty_like(doses)
    for i, dose in enumerate(doses):
        n_particles = dose / m_particle_g
        kinetic_mg = cu_captured_mg * n_particles
        stoich_mg = (dose / mw_oxide) * cu_per_mol * MW_CU * 1e3
        actual_mg = min(kinetic_mg, stoich_mg, TOTAL_CU_MG)
        removals[i] = actual_mg / TOTAL_CU_MG * 100
    return removals


def find_crossover(doses, removals, target):
    """Find dose where removal first crosses target (linear interpolation)."""
    for i in range(len(removals) - 1):
        if removals[i] < target <= removals[i + 1]:
            frac = (target - removals[i]) / (removals[i + 1] - removals[i])
            return doses[i] + frac * (doses[i + 1] - doses[i])
    return None


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    cap_30min = load_dictra_capture(1800)
    cap_1min = load_dictra_capture(60)

    print(f"Per-particle Cu capture at T={T_K}K, R={R_UM}μm:")
    print(f"  30 min: {cap_30min:.6f} mg")
    print(f"   1 min: {cap_1min:.6f} mg")
    print()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), sharey=True)

    panels = [
        (ax1, cap_30min, "30 min", "30-min contact  (stoichiometry-limited)"),
        (ax2, cap_1min, "1 min", "1-min contact  (kinetics-limited)"),
    ]

    for ax, cap, tlabel, title in panels:
        crossovers = []

        for name, rho, cu_per_mol, mw, color, marker in OXIDES:
            removals = compute_removal_curve(DOSES, rho, cu_per_mol, mw, cap)
            ax.plot(DOSES, removals, color=color, linewidth=2.2, label=name,
                    marker=marker, markevery=60, markersize=6, zorder=3)

            xover = find_crossover(DOSES, removals, TARGET_PCT)
            if xover is not None:
                crossovers.append((name, xover, color))

        # ── Target line ────────────────────────────────────────────
        ax.axhline(TARGET_PCT, color="#888888", linestyle="--",
                   linewidth=1.2, alpha=0.7, zorder=1)
        ax.text(19.5, TARGET_PCT + 1.5, f"{TARGET_PCT}%", color="#888888",
                fontsize=9, ha="right", va="bottom", fontstyle="italic")

        # ── Crossover markers + vertical guides ────────────────────
        for name, xover, color in crossovers:
            ax.plot(xover, TARGET_PCT, "X", color=color, markersize=9,
                    markeredgewidth=2, markeredgecolor="white", zorder=5)
            ax.axvline(xover, color=color, linestyle=":", linewidth=0.8,
                       alpha=0.35, zorder=1)

        # ── Crossover dose table ──────────────────────────────────
        if crossovers:
            crossovers.sort(key=lambda x: x[1])
            table_lines = ["Min dose for 66.7%:"]
            for name, xover, color in crossovers:
                table_lines.append(f"  {name:6s}  {xover:5.2f} g")

            table_text = "\n".join(table_lines)
            # 30-min panel: lower-right (curves saturate early, space is open)
            # 1-min panel: upper-right
            tx, ty = (0.97, 0.45) if cap == cap_30min else (0.97, 0.97)
            ax.text(tx, ty, table_text, transform=ax.transAxes,
                    fontsize=8.5, fontfamily="monospace", va="top", ha="right",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                              edgecolor="#cccccc", alpha=0.9), zorder=6)

        # ── Axis formatting ────────────────────────────────────────
        ax.set_xlabel("Oxide dose (g)", fontsize=12)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 105)
        ax.grid(which="major", alpha=0.3, zorder=0)
        ax.grid(which="minor", alpha=0.1, zorder=0)
        ax.minorticks_on()
        for spine in ax.spines.values():
            spine.set_visible(False)

    ax1.set_ylabel("Cu removal (%)", fontsize=12)

    # Single shared legend between panels — place below the title area
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, fontsize=10,
               framealpha=0.9, bbox_to_anchor=(0.5, 0.90))

    fig.suptitle(
        "Dose-Response: Cu Removal vs Oxide Mass\n"
        f"T = {T_K} K,  R = {R_UM} μm,  {STEEL_MASS_KG} kg steel,  "
        f"{CU_INIT_WT} wt% Cu",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.92])

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"dose_response_curves.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"Saved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
