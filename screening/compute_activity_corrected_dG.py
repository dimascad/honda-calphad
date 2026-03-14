"""
Compute activity-corrected dG for ternary reactions under steelmaking conditions.

Our existing dG values assume PURE Cu and PURE O2 as reactants:
    dG_pure = G(CuMOy) - G(Cu_pure) - n*G(O2_pure) - G(MOx_pure)

In real steel, Cu is dilute (X_Cu ~ 0.003, a_Cu << 1) and O2 activity is set
by the deoxidation practice. The effective driving force is:
    dG_eff = dG_pure + RT * ln(a_Cu) + n * RT * ln(pO2/1atm)

Since ln(a_Cu) is negative (a_Cu < 1), the RT*ln(a_Cu) term is POSITIVE,
making reactions LESS favorable. This correction preserves the ranking but
changes which reactions remain thermodynamically viable.

IMPORTANT: For each parent oxide, we evaluate ALL possible products and pick
the one with the most favorable corrected dG. Under dilute Cu conditions,
products consuming fewer Cu atoms are preferred (e.g., CuV2O6 over Cu3V2O8).

Output: data/tcpython/processed/activity_corrected_dG.csv
        figures/dG_corrected_comparison.png + .pdf
        figures/dG_sensitivity_gamma_Cu.png + .pdf
"""

import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# Primary data source: fine-resolution top 6 (25K steps)
CSV_TOP6 = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "dG_vs_T_top6.csv"
# Full data source: all products (50K steps) — for products not in top 6
CSV_FULL = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "ternary_reaction_energies.csv"

CSV_OUT = SCRIPT_DIR.parent / "data" / "tcpython" / "processed" / "activity_corrected_dG.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

R = 8.314  # J/(mol*K)

# Steelmaking Cu level
X_CU = 0.003  # ~0.3 wt% Cu in steel

# For dilute solution in liquid iron, a_Cu = gamma * X_Cu
# gamma_Cu in liquid Fe at 1800K: literature range 5-13 (Raoultian)
# Hino & Ito (2010) recommend ~8.5; Sigworth & Elliott (1974) give ~10
GAMMA_CU = 8.5
A_CU = GAMMA_CU * X_CU  # ~0.0255

# Products and their O2 stoichiometric coefficients in the reaction
# Cu + MOx + n*O2 -> CuMOy
O2_COEFFICIENTS = {
    "CuFe2O4": 1.0,     # Cu + 2FeO + O2 -> CuFe2O4
    "Cu3V2O8": 1.5,     # 3Cu + V2O5 + 1.5O2 -> Cu3V2O8
    "CuV2O6":  0.5,     # Cu + V2O5 + 0.5O2 -> CuV2O6
    "CuMn2O4": 1.0,     # Cu + 2MnO + O2 -> CuMn2O4
    "Cu2SiO4": 1.0,     # 2Cu + SiO2 + O2 -> Cu2SiO4
    "CuB2O4":  0.5,     # Cu + B2O3 + 0.5O2 -> CuB2O4
    "CuAl2O4": 0.5,     # Cu + Al2O3 + 0.5O2 -> CuAl2O4
}

# Number of Cu atoms consumed per formula unit
CU_ATOMS = {
    "CuFe2O4": 1,
    "Cu3V2O8": 3,
    "CuV2O6":  1,
    "CuMn2O4": 1,
    "Cu2SiO4": 2,
    "CuB2O4":  1,
    "CuAl2O4": 1,
}

# Plot order: by corrected dG (most favorable first)
PRODUCT_ORDER = [
    "CuFe2O4", "CuMn2O4", "CuV2O6", "CuB2O4",
    "CuAl2O4", "Cu3V2O8", "Cu2SiO4",
]

COLORS = {
    "CuFe2O4": "#0077BB",
    "Cu3V2O8": "#EE7733",
    "CuV2O6":  "#CC6600",
    "CuMn2O4": "#AA3377",
    "Cu2SiO4": "#009988",
    "CuB2O4":  "#EE3377",
    "CuAl2O4": "#BBBBBB",
}

LINE_STYLES = {
    "CuFe2O4": "-",
    "Cu3V2O8": "--",
    "CuV2O6":  "-.",
    "CuMn2O4": ":",
    "Cu2SiO4": "-.",
    "CuB2O4":  "-",
    "CuAl2O4": "--",
}

SHORT_LABELS = {
    "CuFe2O4": r"CuFe$_2$O$_4$",
    "Cu3V2O8": r"Cu$_3$V$_2$O$_8$",
    "CuV2O6":  r"CuV$_2$O$_6$",
    "CuMn2O4": r"CuMn$_2$O$_4$",
    "Cu2SiO4": r"Cu$_2$SiO$_4$",
    "CuB2O4":  r"CuB$_2$O$_4$",
    "CuAl2O4": r"CuAl$_2$O$_4$",
}

# Parent oxide for each product (for sensitivity analysis grouping)
PARENT_OXIDE = {
    "CuFe2O4": "FeO",
    "Cu3V2O8": "V2O5",
    "CuV2O6":  "V2O5",
    "CuMn2O4": "MnO",
    "Cu2SiO4": "SiO2",
    "CuB2O4":  "B2O3",
    "CuAl2O4": "Al2O3",
}


def load_data():
    """Load dG data from both CSV sources."""
    data = {}

    # First load fine-resolution top-6 data
    if CSV_TOP6.exists():
        with open(CSV_TOP6) as f:
            for r in csv.DictReader(f):
                product = r["product"]
                if product not in O2_COEFFICIENTS:
                    continue
                if product not in data:
                    data[product] = []
                try:
                    T = float(r["T_K"])
                    dG_pure = float(r["dG_rxn_system_kJ"])
                    data[product].append((T, dG_pure))
                except (ValueError, KeyError):
                    pass

    # Then load any missing products from the full ternary CSV
    # Only load products we don't already have from the fine-resolution CSV
    products_from_top6 = set(data.keys())
    if CSV_FULL.exists():
        with open(CSV_FULL) as f:
            for r in csv.DictReader(f):
                product = r.get("product", "")
                if product not in O2_COEFFICIENTS:
                    continue
                if product in products_from_top6:
                    continue  # already have fine-resolution data
                if product not in data:
                    data[product] = []
                try:
                    T = float(r["T_K"])
                    dG_kJ_str = r.get("dG_rxn_system_kJ", "")
                    if not dG_kJ_str:
                        continue
                    dG_pure = float(dG_kJ_str)
                    data[product].append((T, dG_pure))
                except (ValueError, KeyError):
                    pass

    return data


def main():
    print("=" * 70)
    print("Activity-Corrected dG for Ternary Reactions")
    print("=" * 70)
    print("X_Cu = %.4f, gamma_Cu = %.1f, a_Cu = %.4f" % (X_CU, GAMMA_CU, A_CU))
    print("RT*ln(a_Cu) at 1800K = %.1f kJ/mol" % (R * 1800 * math.log(A_CU) / 1000))
    print()

    data = load_data()

    # Report what we loaded
    for product in PRODUCT_ORDER:
        n = len(data.get(product, []))
        src = "top6" if product in ["CuFe2O4", "Cu3V2O8", "CuMn2O4",
                                     "Cu2SiO4", "CuB2O4", "CuAl2O4"] and n > 30 \
              else "ternary_full"
        print("  %-14s: %3d data points (source: %s)" % (product, n, src))
    print()

    # Compute corrections
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    out_rows = []

    print("%-14s  %4s  %8s  %8s  %8s  %8s  %s" % (
        "Product", "nCu", "dG_pure", "Cu_corr", "dG_corr", "dG_air", "Verdict"))
    print("-" * 75)

    for product in PRODUCT_ORDER:
        if product not in data:
            continue

        n_cu = CU_ATOMS[product]
        n_o2 = O2_COEFFICIENTS[product]

        for T, dG_pure in sorted(data[product]):
            # Cu activity correction: Cu is a REACTANT, so lowering its
            # activity raises dG (less favorable). For reaction quotient Q:
            #   dG = dG_pure + RT*ln(Q)
            #   Q = a_products / (a_Cu^n_Cu * a_O2^n_O2 * a_MOx)
            # With a_products=1, a_MOx=1 (pure solid oxide):
            #   RT*ln(Q) = -n_Cu*RT*ln(a_Cu) - n_O2*RT*ln(pO2)
            cu_correction_kJ = -n_cu * R * T * math.log(A_CU) / 1000.0

            # O2 correction at 1 atm: zero (ln(1) = 0)
            # At 0.21 atm: -n_O2 * RT * ln(0.21) > 0 (less favorable)
            o2_correction_air_kJ = -n_o2 * R * T * math.log(0.21) / 1000.0

            # Case A: pO2 = 1 atm, dilute Cu
            dG_corrected_A = dG_pure + cu_correction_kJ

            # Case B: pO2 = 0.21 atm (air), dilute Cu
            dG_corrected_B = dG_pure + cu_correction_kJ + o2_correction_air_kJ

            out_rows.append({
                "product": product,
                "T_K": T,
                "T_C": T - 273.15,
                "dG_pure_kJ": round(dG_pure, 2),
                "Cu_correction_kJ": round(cu_correction_kJ, 2),
                "O2_correction_air_kJ": round(o2_correction_air_kJ, 2),
                "dG_corrected_pO2_1atm_kJ": round(dG_corrected_A, 2),
                "dG_corrected_pO2_air_kJ": round(dG_corrected_B, 2),
                "a_Cu": round(A_CU, 4),
                "n_Cu": n_cu,
                "n_O2": n_o2,
                "parent_oxide": PARENT_OXIDE[product],
                "verdict_corrected": "FAVORABLE" if dG_corrected_A < 0 else "UNFAVORABLE",
            })

            # Print 1800K values
            if abs(T - 1800) < 1:
                verdict = "FAVORABLE" if dG_corrected_A < 0 else "UNFAVORABLE"
                print("%-14s  %4d  %8.1f  %8.1f  %8.1f  %8.1f  %s" % (
                    product, n_cu, dG_pure, cu_correction_kJ,
                    dG_corrected_A, dG_corrected_B, verdict))

    # Write CSV
    fieldnames = [
        "product", "parent_oxide", "T_K", "T_C", "dG_pure_kJ", "Cu_correction_kJ",
        "O2_correction_air_kJ", "dG_corrected_pO2_1atm_kJ",
        "dG_corrected_pO2_air_kJ", "a_Cu", "n_Cu", "n_O2", "verdict_corrected",
    ]
    with open(CSV_OUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print()
    print("CSV saved: %s" % CSV_OUT)

    # ==========================================================================
    # Plot 1: Pure vs Corrected comparison (both panels)
    # ==========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for product in PRODUCT_ORDER:
        if product not in data:
            continue

        pts = sorted(data[product])
        T_arr = np.array([p[0] for p in pts])
        dG_arr = np.array([p[1] for p in pts])
        T_C = T_arr - 273.15

        n_cu = CU_ATOMS[product]
        # Correction: -n_Cu * RT * ln(a_Cu) is POSITIVE (makes dG less negative)
        cu_corr = -n_cu * R * T_arr * np.log(A_CU) / 1000.0
        dG_corrected = dG_arr + cu_corr

        # Left panel: pure reference
        ax1.plot(T_C, dG_arr,
                 color=COLORS[product],
                 linestyle=LINE_STYLES[product],
                 linewidth=1.8,
                 label=SHORT_LABELS[product])

        # Right panel: activity-corrected
        ax2.plot(T_C, dG_corrected,
                 color=COLORS[product],
                 linestyle=LINE_STYLES[product],
                 linewidth=1.8,
                 label=SHORT_LABELS[product])

    for ax in [ax1, ax2]:
        ax.axhline(y=0, color='black', linewidth=0.8, linestyle='-', alpha=0.5)
        ax.axvspan(1500, 1650, color='#CCCCCC', alpha=0.25, zorder=0)
        ax.set_xlabel(r"Temperature ($^\circ$C)", fontsize=12)
        ax.set_ylabel(r"$\Delta G_{\mathrm{rxn}}$ (kJ/mol)", fontsize=12)
        ax.grid(True, which='major', alpha=0.3)
        ax.minorticks_on()
        ax.grid(True, which='minor', alpha=0.1)
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Set y-limits after plotting so text placement works
    for ax in [ax1, ax2]:
        ymin, ymax = ax.get_ylim()
        ax.text(1575, ymax - 0.05 * (ymax - ymin), "Steelmaking\nrange",
                fontsize=8, color='#777777', ha='center', va='top', style='italic')

    ax1.set_title("Pure Reference States\n" + r"($a_{\mathrm{Cu}}$ = 1)", fontsize=11)
    ax2.set_title("Steelmaking Conditions\n" +
                   r"($a_{\mathrm{Cu}}$ = %.4f, X$_{\mathrm{Cu}}$ = %.3f)" % (A_CU, X_CU),
                   fontsize=11)

    ax1.legend(fontsize=7, loc='lower right', framealpha=0.9, edgecolor='#CCCCCC')
    ax2.legend(fontsize=7, loc='lower left', framealpha=0.9, edgecolor='#CCCCCC')

    plt.tight_layout()

    png_path = FIG_DIR / "dG_corrected_comparison.png"
    pdf_path = FIG_DIR / "dG_corrected_comparison.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)

    print("Figure saved: %s" % png_path)
    print("Figure saved: %s" % pdf_path)

    # ==========================================================================
    # Plot 2: gamma_Cu sensitivity analysis at 1800K
    # ==========================================================================
    gamma_range = np.linspace(3.0, 15.0, 50)
    T_sens = 1800.0

    # Get dG_pure at 1800K for each product
    dG_pure_1800 = {}
    for product in PRODUCT_ORDER:
        if product not in data:
            continue
        for T, dG in data[product]:
            if abs(T - T_sens) < 1:
                dG_pure_1800[product] = dG
                break

    fig2, ax3 = plt.subplots(1, 1, figsize=(8, 5.5))

    for product in PRODUCT_ORDER:
        if product not in dG_pure_1800:
            continue

        dG_pure = dG_pure_1800[product]
        n_cu = CU_ATOMS[product]

        dG_eff = np.array([
            dG_pure + (-n_cu * R * T_sens * math.log(g * X_CU) / 1000.0)
            for g in gamma_range
        ])

        ax3.plot(gamma_range, dG_eff,
                 color=COLORS[product],
                 linestyle=LINE_STYLES[product],
                 linewidth=1.8,
                 label="%s (n$_{Cu}$=%d)" % (SHORT_LABELS[product], n_cu))

    ax3.axhline(y=0, color='black', linewidth=0.8, linestyle='-', alpha=0.5)
    ax3.axvspan(7.0, 10.0, color='#CCCCCC', alpha=0.2, zorder=0,
                label=r"Literature $\gamma_{\mathrm{Cu}}$ range")
    ax3.axvline(x=GAMMA_CU, color='black', linewidth=0.5, linestyle='--', alpha=0.4)

    ax3.set_xlabel(r"$\gamma_{\mathrm{Cu}}$ (Raoultian activity coefficient)", fontsize=12)
    ax3.set_ylabel(r"$\Delta G_{\mathrm{eff}}$ at 1800 K (kJ/mol)", fontsize=12)
    ax3.set_title(r"Sensitivity to $\gamma_{\mathrm{Cu}}$ at 1800 K, $X_{\mathrm{Cu}}$ = 0.003",
                  fontsize=11)
    ax3.legend(fontsize=7, loc='upper left', framealpha=0.9, edgecolor='#CCCCCC')
    ax3.grid(True, which='major', alpha=0.3)
    ax3.minorticks_on()
    ax3.grid(True, which='minor', alpha=0.1)
    for spine in ax3.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    sens_png = FIG_DIR / "dG_sensitivity_gamma_Cu.png"
    sens_pdf = FIG_DIR / "dG_sensitivity_gamma_Cu.pdf"
    fig2.savefig(sens_png, dpi=300, bbox_inches='tight')
    fig2.savefig(sens_pdf, bbox_inches='tight')
    plt.close(fig2)

    print("Figure saved: %s" % sens_png)
    print("Figure saved: %s" % sens_pdf)

    # ==========================================================================
    # Summary at 1800K
    # ==========================================================================
    print()
    print("=" * 75)
    print("RANKING AT 1800K - Activity-Corrected (a_Cu = %.4f)" % A_CU)
    print("=" * 75)
    print()

    results_1800 = [(r["product"], r["n_Cu"], r["dG_pure_kJ"],
                     r["dG_corrected_pO2_1atm_kJ"])
                    for r in out_rows if abs(r["T_K"] - 1800) < 1]
    results_1800.sort(key=lambda x: x[3])

    print("%-4s %-14s %4s %10s %12s %10s" % (
        "Rank", "Product", "nCu", "dG_pure", "dG_corrected", "Status"))
    print("-" * 60)
    for i, (product, n_cu, dG_pure, dG_corr) in enumerate(results_1800, 1):
        if dG_corr < -10:
            status = "ROBUST"
        elif dG_corr < 0:
            status = "MARGINAL"
        elif dG_corr < 15:
            status = "UNCERTAIN"
        else:
            status = "UNFAVORABLE"
        print("%-4d %-14s %4d %10.1f %12.1f %10s" % (
            i, product, n_cu, dG_pure, dG_corr, status))

    n_favorable = sum(1 for _, _, _, dG in results_1800 if dG < 0)
    n_uncertain = sum(1 for _, _, _, dG in results_1800 if 0 <= dG < 15)
    n_unfavorable = sum(1 for _, _, _, dG in results_1800 if dG >= 15)
    print()
    print("%d favorable, %d uncertain (within gamma_Cu error), %d unfavorable" % (
        n_favorable, n_uncertain, n_unfavorable))

    # V2O5 comparison: which product is preferred?
    print()
    print("=" * 75)
    print("V2O5 PRODUCTS: Cu3V2O8 vs CuV2O6")
    print("=" * 75)
    for product in ["Cu3V2O8", "CuV2O6"]:
        for r in out_rows:
            if r["product"] == product and abs(r["T_K"] - 1800) < 1:
                print("  %-14s: n_Cu=%d, dG_pure=%+.1f, correction=%+.1f, dG_eff=%+.1f kJ" % (
                    product, r["n_Cu"], r["dG_pure_kJ"],
                    r["Cu_correction_kJ"], r["dG_corrected_pO2_1atm_kJ"]))
    print("  Under dilute Cu, CuV2O6 (1 Cu) is preferred over Cu3V2O8 (3 Cu)")
    print("  At Bureau of Mines conditions (~1 wt%% Cu, a_Cu~0.13):")
    for product in ["Cu3V2O8", "CuV2O6"]:
        if product in dG_pure_1800:
            n_cu = CU_ATOMS[product]
            a_cu_bom = 8.5 * 0.015  # ~1 wt% Cu
            corr = -n_cu * R * 1800 * math.log(a_cu_bom) / 1000.0
            dG_eff_bom = dG_pure_1800[product] + corr
            print("    %-14s: dG_eff = %+.1f kJ (a_Cu=%.3f) -> %s" % (
                product, dG_eff_bom, a_cu_bom,
                "FAVORABLE" if dG_eff_bom < 0 else "UNFAVORABLE"))

    print("=" * 75)


if __name__ == "__main__":
    main()
