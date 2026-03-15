#!/usr/bin/env python3
"""
Break-Even Contour Map: feasible operating window for Cu removal.

2D filled contour of Cu removal % over (dose × radius) for Fe₂O₃ at
T=1823K, t=30min. The 66.7% target contour is highlighted — everything
below-left of that line is the feasible operating window.

Overlay: 66.7% contour for all 5 oxides on the same plot, showing how
oxide choice shifts the feasible boundary. Lower-density oxides (SiO₂)
need less mass; higher cu_per_mol oxides (V₂O₅) also shift left.

Per-particle Cu capture is interpolated (log-linear in radius) between
the 5 DICTRA data points (R = 25, 50, 100, 250, 500 μm).

Outputs: figures/breakeven_contour.png, .pdf
Run: python3 screening/visualizations/breakeven_contour.py
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import interp1d
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
TIME_S = 1800  # 30 min

# ── Oxide database ─────────────────────────────────────────────────
# (name, density kg/m³, cu_per_mol, MW g/mol, color, linestyle)
OXIDES = [
    ("Fe₂O₃",  5240, 1.0, 159.69, "#0077BB", "-"),
    ("V₂O₅",   3357, 3.0, 181.88, "#EE7733", "--"),
    ("MnO",    5430, 0.5,  70.94, "#AA3377", "-."),
    ("SiO₂",   2650, 2.0,  60.08, "#009988", ":"),
    ("Al₂O₃",  3950, 1.0, 101.96, "#CC3311", (0, (3, 1, 1, 1))),
]

# ── Grid ───────────────────────────────────────────────────────────
DOSE_RANGE = np.linspace(0.1, 20, 300)
RADIUS_RANGE = np.linspace(20, 550, 300)  # μm


# ══════════════════════════════════════════════════════════════════
# DATA & INTERPOLATION
# ══════════════════════════════════════════════════════════════════

def load_captures():
    """Load per-particle Cu capture for each radius at T=1823K, t=1800s."""
    radii_cap = {}
    with open(SUMMARY_CSV) as f:
        for row in csv.DictReader(f):
            T = float(row["temp_K"])
            R = float(row["radius_um"])
            t = float(row["time_s"])
            if abs(T - T_K) < 1 and abs(t - TIME_S) < 1:
                radii_cap[R] = float(row["cu_captured_mg"])
    return radii_cap


def build_capture_interpolator(radii_cap):
    """Build log-linear interpolator for cu_captured_mg vs radius."""
    rs = sorted(radii_cap.keys())
    caps = [radii_cap[r] for r in rs]
    # Log-linear interpolation (capture scales roughly with surface area)
    interp = interp1d(np.log(rs), np.log(caps), kind="linear",
                      fill_value="extrapolate")
    return lambda r: np.exp(interp(np.log(r)))


def compute_removal_grid(dose_arr, radius_arr, rho, cu_per_mol, mw_oxide,
                         cap_func):
    """Compute removal % on a 2D grid of (dose, radius)."""
    D, R = np.meshgrid(dose_arr, radius_arr)
    # Per-particle capture at each radius
    cap = cap_func(R)
    # Particle count
    r_m = R * 1e-6
    v_particle = (4 / 3) * np.pi * r_m ** 3
    m_particle_g = rho * v_particle * 1e3
    n_particles = D / m_particle_g
    # Kinetic and stoichiometric limits
    kin = cap * n_particles
    stoich = (D / mw_oxide) * cu_per_mol * MW_CU * 1e3
    actual = np.minimum(np.minimum(kin, stoich), TOTAL_CU_MG)
    removal = actual / TOTAL_CU_MG * 100
    return D, R, removal


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    radii_cap = load_captures()
    cap_func = build_capture_interpolator(radii_cap)

    print(f"DICTRA captures at T={T_K}K, t={TIME_S}s:")
    for r in sorted(radii_cap):
        print(f"  R={r:>5.0f} μm: {radii_cap[r]:.6f} mg")

    # ── Compute Fe₂O₃ grid for filled contour ─────────────────────
    fe_rho, fe_cu, fe_mw = 5240, 1.0, 159.69
    D, R, Z_fe = compute_removal_grid(DOSE_RANGE, RADIUS_RANGE,
                                       fe_rho, fe_cu, fe_mw, cap_func)

    # ── Figure ─────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7))

    # Filled contour (Fe₂O₃ background)
    levels = [0, 10, 25, 50, 66.7, 80, 90, 100]
    cmap = plt.cm.Blues
    cf = ax.contourf(D, R, Z_fe, levels=levels, cmap=cmap, alpha=0.7,
                     zorder=1)
    cbar = fig.colorbar(cf, ax=ax, label="Cu removal % (Fe₂O₃)", pad=0.02)
    cbar.set_ticks(levels)

    # Contour lines for Fe₂O₃ (thin)
    cs_thin = ax.contour(D, R, Z_fe, levels=[10, 25, 50, 80, 90],
                         colors="#333333", linewidths=0.5, alpha=0.4,
                         zorder=2)
    ax.clabel(cs_thin, inline=True, fontsize=7, fmt="%.0f%%")

    # ── 66.7% contour for ALL 5 oxides ────────────────────────────
    for name, rho, cu_per_mol, mw, color, ls in OXIDES:
        _, _, Z = compute_removal_grid(DOSE_RANGE, RADIUS_RANGE,
                                       rho, cu_per_mol, mw, cap_func)
        cs = ax.contour(D, R, Z, levels=[TARGET_PCT],
                        colors=[color], linewidths=2.5, linestyles=[ls],
                        zorder=3)
        # Label the contour
        if cs.allsegs[0]:
            seg = cs.allsegs[0][0]
            # Place label at a point along the contour
            idx = len(seg) // 3
            ax.annotate(name, xy=(seg[idx, 0], seg[idx, 1]),
                        fontsize=9, fontweight="bold", color=color,
                        bbox=dict(boxstyle="round,pad=0.2",
                                  facecolor="white", edgecolor=color,
                                  alpha=0.85),
                        zorder=5)

    # ── Mark DICTRA data points ────────────────────────────────────
    for r in radii_cap:
        ax.axhline(r, color="#999999", linewidth=0.3, linestyle="-",
                   zorder=0)

    # ── Feasible region annotation ─────────────────────────────────
    ax.annotate("FEASIBLE\n(≥ 66.7%)", xy=(8, 80), fontsize=12,
                fontweight="bold", color="white", alpha=0.9,
                ha="center", va="center", zorder=4)
    ax.annotate("INFEASIBLE\n(< 66.7%)", xy=(5, 500), fontsize=12,
                fontweight="bold", color="#CC3311", alpha=0.6,
                ha="center", va="center", zorder=4)

    # ── Formatting ─────────────────────────────────────────────────
    ax.set_xlabel("Oxide dose (g)", fontsize=12)
    ax.set_ylabel("Particle radius (μm)", fontsize=12)
    ax.set_xlim(0.1, 20)
    ax.set_ylim(20, 550)
    ax.grid(which="major", alpha=0.2, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.set_title(
        "Break-Even Contour: Feasible Operating Window for 66.7% Cu Removal\n"
        f"T = {T_K} K,  t = {TIME_S // 60} min,  0.5 kg steel,  "
        f"{CU_INIT_WT} wt% Cu",
        fontsize=12, fontweight="bold", pad=12,
    )

    plt.tight_layout()

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"breakeven_contour.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"Saved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
