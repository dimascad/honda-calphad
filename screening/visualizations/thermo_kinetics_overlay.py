#!/usr/bin/env python3
"""
Thermo × Kinetics Overlay: dG vs kinetic removal scatter.

X-axis: |ΔG| at 1800K (thermodynamic driving force, oxide-specific).
Y-axis: Cu removal % at reference conditions (kinetic performance).

Each oxide appears as a connected series of 4 markers (1 min → 30 min),
showing how removal evolves over time. The ideal oxide sits in the
top-right corner: strong ΔG AND high removal.

The key insight: thermodynamics and kinetics are partially decoupled.
Fe₂O₃ has the strongest ΔG but not the highest removal (dense, heavy
particles → fewer per gram). SiO₂ has the weakest ΔG of the strong
tier but the highest removal (light, high Cu capacity).

Reference: T=1823K, R=250μm, dose=3g, 0.5 kg steel, 0.30 wt% Cu.

Outputs: figures/thermo_kinetics_overlay.png, .pdf
Run: python3 screening/visualizations/thermo_kinetics_overlay.py
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
CU_INIT_WT = 0.30
TOTAL_CU_MG = STEEL_MASS_KG * 1e3 * CU_INIT_WT / 100 * 1e3  # 1500 mg
MW_CU = 63.546
TARGET_PCT = 66.7
T_K = 1823
R_UM = 250
DOSE_G = 3.0

# ── Oxide database ─────────────────────────────────────────────────
# (name, dG_kJ, rho_kg/m3, cu_per_mol, MW_g/mol, color)
OXIDES = [
    ("Fe₂O₃",  -111.9, 5240, 1.0, 159.69, "#0077BB"),
    ("V₂O₅",   -109.2, 3357, 3.0, 181.88, "#EE7733"),
    ("MnO",     -63.5, 5430, 0.5,  70.94, "#AA3377"),
    ("SiO₂",    -50.2, 2650, 2.0,  60.08, "#009988"),
    ("Al₂O₃",   -35.7, 3950, 1.0, 101.96, "#CC3311"),
]

TIMES = [60, 300, 600, 1800]
TIME_LABELS = ["1 min", "5 min", "10 min", "30 min"]


# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════

def load_captures():
    """Load per-particle Cu capture for each time at T=1823K, R=250μm."""
    caps = {}
    with open(SUMMARY_CSV) as f:
        for row in csv.DictReader(f):
            T = float(row["temp_K"])
            R = float(row["radius_um"])
            t = float(row["time_s"])
            if abs(T - T_K) < 1 and abs(R - R_UM) < 1:
                caps[int(t)] = float(row["cu_captured_mg"])
    return caps


def removal_pct(cap, rho, cu_per_mol, mw_oxide):
    r_m = R_UM * 1e-6
    v = (4 / 3) * math.pi * r_m ** 3
    m_p = rho * v * 1e3
    n = DOSE_G / m_p
    kin = cap * n
    stoich = (DOSE_G / mw_oxide) * cu_per_mol * MW_CU * 1e3
    return min(kin, stoich, TOTAL_CU_MG) / TOTAL_CU_MG * 100


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    caps = load_captures()
    print(f"Per-particle capture at T={T_K}K, R={R_UM}μm:")
    for t in TIMES:
        print(f"  t={t:>4}s: {caps[t]:.6f} mg")
    print()

    fig, ax = plt.subplots(figsize=(10, 7))

    # ── Plot each oxide as a connected time series ─────────────────
    for name, dG, rho, cu_per_mol, mw, color in OXIDES:
        x = abs(dG)
        ys = [removal_pct(caps[t], rho, cu_per_mol, mw) for t in TIMES]
        sizes = [40, 70, 110, 160]  # growing markers for longer times

        # Connecting line (faint)
        ax.plot([x] * len(ys), ys, color=color, linewidth=1.5, alpha=0.4,
                zorder=2)

        # Markers — all circles, bigger = longer contact time
        for i, (y, sz) in enumerate(zip(ys, sizes)):
            ax.scatter(x, y, s=sz, color=color, marker="o",
                       edgecolors="white", linewidth=0.8, zorder=4)

        # Label at the 30-min point (top of each series)
        ax.annotate(name, xy=(x, ys[-1]), xytext=(6, 6),
                    textcoords="offset points", fontsize=10,
                    fontweight="bold", color=color,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=color, alpha=0.85),
                    zorder=5)

        # Print
        print(f"{name:6s}: |dG|={x:5.1f}, removal @ "
              + ", ".join(f"{t//60}min={y:.1f}%" for t, y in zip(TIMES, ys)))

    # ── Target line ────────────────────────────────────────────────
    ax.axhline(TARGET_PCT, color="#888888", linestyle="--", linewidth=1.2,
               alpha=0.6, zorder=1)
    ax.text(115, TARGET_PCT + 1.2, f"{TARGET_PCT}% target",
            fontsize=9, color="#888888", fontstyle="italic", ha="right")

    # ── Quadrant shading ──────────────────────────────────────────
    # Top-right = ideal (strong dG + high removal)
    ax.axvspan(70, 120, ymin=TARGET_PCT / 80, ymax=1.0, alpha=0.04,
               color="#009988", zorder=0)
    ax.text(95, 82, "IDEAL\nStrong ΔG + High removal",
            fontsize=9, color="#009988", alpha=0.7, ha="center",
            fontstyle="italic", fontweight="bold", zorder=1)

    # ── Time legend (marker sizes) ─────────────────────────────────
    # Show growing circles to indicate size = contact time
    legend_x, legend_y = 38, 72
    ax.text(legend_x, legend_y + 3.5, "Marker size = contact time:",
            fontsize=8.5, fontweight="bold", color="#555555")
    for i, (sz, lbl) in enumerate(zip(sizes, TIME_LABELS)):
        ax.scatter(legend_x + i * 7, legend_y, s=sz, color="#888888",
                   marker="o", edgecolors="#555555", linewidth=0.5, zorder=3)
        ax.text(legend_x + i * 7, legend_y - 4, lbl, fontsize=7,
                ha="center", color="#888888")
    ax.text(legend_x + 10.5, legend_y - 8, "(shape identifies oxide — see labels)",
            fontsize=7, color="#aaaaaa", fontstyle="italic")

    # ── Formatting ─────────────────────────────────────────────────
    ax.set_xlabel("|ΔG| at 1800 K (kJ/mol)", fontsize=12)
    ax.set_ylabel("Cu removal (%)", fontsize=12)
    ax.set_xlim(30, 118)
    ax.set_ylim(0, 90)
    ax.grid(which="major", alpha=0.3, zorder=0)
    ax.grid(which="minor", alpha=0.1, zorder=0)
    ax.minorticks_on()
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(
        "Thermo × Kinetics: Driving Force vs Removal Performance\n"
        f"T = {T_K} K,  R = {R_UM} μm,  dose = {DOSE_G} g,  "
        f"0.5 kg steel,  {CU_INIT_WT} wt% Cu",
        fontsize=12, fontweight="bold", pad=12,
    )

    plt.tight_layout()

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"thermo_kinetics_overlay.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"\nSaved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
