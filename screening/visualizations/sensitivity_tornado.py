#!/usr/bin/env python3
"""
Sensitivity Tornado Chart: which parameter has the biggest effect on Cu removal?

Baseline: T=1823K, R=250μm, t=600s, dose=3g Fe₂O₃ → 16.4% removal.
Each parameter is perturbed to practical low/high bounds (one at a time)
while all others are held at baseline. The bar width = total swing in
removal %, sorted widest at top.

Key insights:
  - Particle radius dominates: halving R from 250→50μm gives 8x more
    particles per gram, pushing removal from 16% to 80%.
  - Temperature below the liquidus (~1811K) kills performance entirely
    (D_Cu drops ~260x from liquid to solid).
  - Oxide choice has the smallest effect — all 5 candidates are within
    ~16 pp of each other. The real levers are particle size and dose.

Outputs: figures/sensitivity_tornado.png, .pdf
Run: python3 screening/visualizations/sensitivity_tornado.py
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

# ── Baseline ───────────────────────────────────────────────────────
T_BASE = 1823       # K
R_BASE = 250        # μm
T_BASE_S = 600      # s (10 min)
DOSE_BASE = 3.0     # g
RHO_BASE = 5240     # kg/m³ (Fe₂O₃)
CU_PER_MOL_BASE = 1.0
MW_OX_BASE = 159.69  # g/mol Fe₂O₃

# ── Colors ─────────────────────────────────────────────────────────
CLR_DOWN = "#CC3311"   # red — downside risk
CLR_UP = "#0077BB"     # blue — upside gain


# ══════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════

def load_data():
    rows = []
    with open(SUMMARY_CSV) as f:
        for row in csv.DictReader(f):
            rows.append({
                "T": float(row["temp_K"]),
                "R": float(row["radius_um"]),
                "t": float(row["time_s"]),
                "cap": float(row["cu_captured_mg"]),
            })
    return rows

DATA = []  # populated in main()


def get_cap(T, R, t):
    for d in DATA:
        if abs(d["T"] - T) < 1 and abs(d["R"] - R) < 1 and abs(d["t"] - t) < 1:
            return d["cap"]
    return None


def removal_pct(T, R, t, dose, rho=RHO_BASE, cu_per_mol=CU_PER_MOL_BASE,
                mw=MW_OX_BASE):
    cap = get_cap(T, R, t)
    if cap is None:
        return None
    r_m = R * 1e-6
    v = (4 / 3) * math.pi * r_m ** 3
    m_p = rho * v * 1e3  # grams per particle
    n = dose / m_p
    kin = cap * n
    stoich = (dose / mw) * cu_per_mol * MW_CU * 1e3
    return min(kin, stoich, TOTAL_CU_MG) / TOTAL_CU_MG * 100


# ══════════════════════════════════════════════════════════════════
# TORNADO
# ══════════════════════════════════════════════════════════════════

def main():
    global DATA
    DATA = load_data()

    base_pct = removal_pct(T_BASE, R_BASE, T_BASE_S, DOSE_BASE)
    print(f"Baseline: T={T_BASE}K, R={R_BASE}μm, t={T_BASE_S}s, "
          f"dose={DOSE_BASE}g Fe₂O₃ → {base_pct:.1f}%")

    # Define perturbations: (label, low_label, low_pct, high_label, high_pct)
    perturbations = []

    # 1. Temperature: 1773K (below liquidus) → 1873K
    lo = removal_pct(1773, R_BASE, T_BASE_S, DOSE_BASE)
    hi = removal_pct(1873, R_BASE, T_BASE_S, DOSE_BASE)
    perturbations.append(("Temperature", "1773 K\n(solid)", lo,
                          "1873 K", hi))

    # 2. Particle radius: 500μm (coarse) → 50μm (fine)
    lo = removal_pct(T_BASE, 500, T_BASE_S, DOSE_BASE)
    hi = removal_pct(T_BASE, 50, T_BASE_S, DOSE_BASE)
    perturbations.append(("Particle radius", "500 μm", lo,
                          "50 μm", hi))

    # 3. Contact time: 60s → 1800s
    lo = removal_pct(T_BASE, R_BASE, 60, DOSE_BASE)
    hi = removal_pct(T_BASE, R_BASE, 1800, DOSE_BASE)
    perturbations.append(("Contact time", "1 min", lo,
                          "30 min", hi))

    # 4. Oxide dose: 1g → 10g
    lo = removal_pct(T_BASE, R_BASE, T_BASE_S, 1.0)
    hi = removal_pct(T_BASE, R_BASE, T_BASE_S, 10.0)
    perturbations.append(("Oxide dose", "1 g", lo,
                          "10 g", hi))

    # 5. Oxide choice: MnO (worst) → SiO₂ (best)
    lo = removal_pct(T_BASE, R_BASE, T_BASE_S, DOSE_BASE,
                     rho=5430, cu_per_mol=0.5, mw=70.94)   # MnO
    hi = removal_pct(T_BASE, R_BASE, T_BASE_S, DOSE_BASE,
                     rho=2650, cu_per_mol=2.0, mw=60.08)   # SiO₂
    perturbations.append(("Oxide choice", "MnO", lo,
                          "SiO₂", hi))

    # Sort by total swing (widest bar at top)
    perturbations.sort(key=lambda p: -(p[3 + 1] - p[2]))

    # ── Print summary ──────────────────────────────────────────────
    print(f"\n{'Parameter':<18} {'Low':>10} {'Low %':>8} {'High':>10} "
          f"{'High %':>8} {'Swing':>8}")
    print("-" * 66)
    for label, lo_lbl, lo_pct, hi_lbl, hi_pct in perturbations:
        lo_lbl_clean = lo_lbl.replace("\n", " ")
        hi_lbl_clean = hi_lbl.replace("\n", " ")
        print(f"{label:<18} {lo_lbl_clean:>10} {lo_pct:7.1f}% "
              f"{hi_lbl_clean:>10} {hi_pct:7.1f}% {hi_pct - lo_pct:7.1f} pp")

    # ── Build figure ───────────────────────────────────────────────
    n_params = len(perturbations)
    fig, ax = plt.subplots(figsize=(10, 5.5))

    y_positions = np.arange(n_params)[::-1]  # top-to-bottom, widest first
    bar_height = 0.55

    for i, (label, lo_lbl, lo_pct, hi_lbl, hi_pct) in enumerate(perturbations):
        y = y_positions[i]

        # Downside bar (baseline → low)
        if lo_pct < base_pct:
            ax.barh(y, lo_pct - base_pct, height=bar_height, left=base_pct,
                    color=CLR_DOWN, edgecolor="white", linewidth=0.5, zorder=3)
            # Place percentage inside bar if there's room, else outside
            txt_x = lo_pct + 0.5 if (base_pct - lo_pct) > 8 else lo_pct - 0.8
            txt_ha = "left" if (base_pct - lo_pct) > 8 else "right"
            txt_clr = "white" if (base_pct - lo_pct) > 8 else CLR_DOWN
            ax.text(txt_x, y, f"{lo_pct:.1f}%",
                    ha=txt_ha, va="center", fontsize=8.5, color=txt_clr,
                    fontweight="bold")
            # Low label below the bar
            ax.text(lo_pct - 0.8, y - 0.30, lo_lbl,
                    ha="right", va="top", fontsize=7.5, color="#666666")

        # Upside bar (baseline → high)
        if hi_pct > base_pct:
            ax.barh(y, hi_pct - base_pct, height=bar_height, left=base_pct,
                    color=CLR_UP, edgecolor="white", linewidth=0.5, zorder=3)
            ax.text(hi_pct + 0.8, y, f"{hi_pct:.1f}%",
                    ha="left", va="center", fontsize=8.5, color=CLR_UP,
                    fontweight="bold")
            # High label on the outer edge
            ax.text(hi_pct + 0.8, y - 0.30, hi_lbl,
                    ha="left", va="top", fontsize=7.5, color="#666666")

    # ── Baseline vertical line ─────────────────────────────────────
    ax.axvline(base_pct, color="#333333", linewidth=1.5, linestyle="-",
               zorder=4)
    ax.text(base_pct, -0.8, f"Baseline: {base_pct:.1f}%",
            ha="center", va="top", fontsize=9, fontweight="bold",
            color="#333333")

    # ── Y-axis labels ──────────────────────────────────────────────
    ax.set_yticks(y_positions)
    ax.set_yticklabels([p[0] for p in perturbations], fontsize=11)

    # ── Formatting ─────────────────────────────────────────────────
    ax.set_xlabel("Cu removal (%)", fontsize=12)
    ax.set_xlim(-2, 85)
    ax.set_ylim(-1.2, n_params - 0.5)
    ax.grid(which="major", axis="x", alpha=0.3, zorder=0)
    ax.grid(which="minor", axis="x", alpha=0.1, zorder=0)
    ax.xaxis.set_minor_locator(plt.MultipleLocator(5))
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="y", which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # ── Legend ─────────────────────────────────────────────────────
    patch_down = mpatches.Patch(color=CLR_DOWN, label="Downside (worse)")
    patch_up = mpatches.Patch(color=CLR_UP, label="Upside (better)")
    ax.legend(handles=[patch_up, patch_down], loc="lower right",
              fontsize=9, framealpha=0.9)

    # ── Title ──────────────────────────────────────────────────────
    ax.set_title(
        "Sensitivity Tornado: One-at-a-Time Perturbations from Baseline\n"
        f"Baseline: T={T_BASE}K, R={R_BASE}μm, t={T_BASE_S//60}min, "
        f"dose={DOSE_BASE}g Fe₂O₃, 0.5kg steel, {CU_INIT_WT}wt% Cu",
        fontsize=12, fontweight="bold", pad=12,
    )

    plt.tight_layout()

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"sensitivity_tornado.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"Saved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
