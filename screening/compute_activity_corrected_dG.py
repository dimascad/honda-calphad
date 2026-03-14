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

For the oxide reference, we keep the pure oxide (activity = 1) since we're
adding solid oxide powder, not dissolved oxide.

For O2, at steelmaking conditions pO2 is very low (~1e-10 atm for Al-killed
steel), but in our reaction framework O2 is consumed from the atmosphere or
slag, not the steel. We compute two cases:
  Case A: pO2 = 1 atm (as in our existing calculations)
  Case B: pO2 = 0.21 atm (air)

The dominant correction is the Cu activity term.

Output: data/tcpython/processed/activity_corrected_dG.csv
        figures/dG_corrected_comparison.png + .pdf
"""

import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "dG_vs_T_top6.csv"
CSV_OUT = SCRIPT_DIR.parent / "data" / "tcpython" / "processed" / "activity_corrected_dG.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

R = 8.314  # J/(mol*K)

# Steelmaking Cu level
X_CU = 0.003  # ~0.3 wt% Cu in steel

# For dilute solution in liquid iron, a_Cu ≈ gamma * X_Cu
# gamma_Cu in liquid Fe at 1800K is approximately 8-10 (Raoultian)
# Using gamma = 8.5 as a reasonable estimate from literature
GAMMA_CU = 8.5
A_CU = GAMMA_CU * X_CU  # ~0.0255

# Products and their O2 stoichiometric coefficients in the reaction
# Cu + MOx + n*O2 -> CuMOy
O2_COEFFICIENTS = {
    "CuFe2O4": 1.0,     # Cu + 2FeO + O2 -> CuFe2O4
    "Cu3V2O8": 1.5,     # 3Cu + V2O5 + 1.5O2 -> Cu3V2O8 (need to check)
    "CuMn2O4": 1.0,     # Cu + 2MnO + O2 -> CuMn2O4
    "Cu2SiO4": 1.0,     # 2Cu + SiO2 + O2 -> Cu2SiO4 (need to check)
    "CuB2O4": 0.5,      # Cu + B2O3 + 0.5O2 -> CuB2O4
    "CuAl2O4": 0.5,     # Cu + Al2O3 + 0.5O2 -> CuAl2O4
}

# Number of Cu atoms consumed per formula unit
CU_ATOMS = {
    "CuFe2O4": 1,
    "Cu3V2O8": 3,
    "CuMn2O4": 1,
    "Cu2SiO4": 2,
    "CuB2O4": 1,
    "CuAl2O4": 1,
}

PRODUCT_ORDER = ["CuFe2O4", "Cu3V2O8", "CuMn2O4", "Cu2SiO4", "CuB2O4", "CuAl2O4"]

COLORS = {
    "CuFe2O4": "#0077BB",
    "Cu3V2O8": "#EE7733",
    "CuMn2O4": "#AA3377",
    "Cu2SiO4": "#009988",
    "CuB2O4":  "#EE3377",
    "CuAl2O4": "#BBBBBB",
}

LINE_STYLES = {
    "CuFe2O4": "-",
    "Cu3V2O8": "--",
    "CuMn2O4": ":",
    "Cu2SiO4": "-.",
    "CuB2O4":  "-",
    "CuAl2O4": "--",
}

SHORT_LABELS = {
    "CuFe2O4": r"CuFe$_2$O$_4$",
    "Cu3V2O8": r"Cu$_3$V$_2$O$_8$",
    "CuMn2O4": r"CuMn$_2$O$_4$",
    "Cu2SiO4": r"Cu$_2$SiO$_4$",
    "CuB2O4":  r"CuB$_2$O$_4$",
    "CuAl2O4": r"CuAl$_2$O$_4$",
}


def main():
    print("=" * 70)
    print("Activity-Corrected dG for Ternary Reactions")
    print("=" * 70)
    print("X_Cu = %.4f, gamma_Cu = %.1f, a_Cu = %.4f" % (X_CU, GAMMA_CU, A_CU))
    print("RT*ln(a_Cu) at 1800K = %.1f kJ/mol" % (R * 1800 * math.log(A_CU) / 1000))
    print()

    # Read existing dG data
    with open(CSV_IN) as f:
        rows = list(csv.DictReader(f))

    # Group by product
    data = {}
    for r in rows:
        product = r["product"]
        if product not in PRODUCT_ORDER:
            continue
        if product not in data:
            data[product] = []
        try:
            T = float(r["T_K"])
            dG_pure = float(r["dG_rxn_system_kJ"])
            data[product].append((T, dG_pure))
        except (ValueError, KeyError):
            pass

    # Compute corrections
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    out_rows = []

    print("%-14s  %8s  %8s  %8s  %8s  %s" % (
        "Product", "dG_pure", "Cu_corr", "dG_corr", "dG_corr", "Verdict"))
    print("%-14s  %8s  %8s  %8s  %8s" % (
        "", "(kJ)", "(kJ)", "(kJ)", "@1800K"))
    print("-" * 70)

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
                "verdict_corrected": "FAVORABLE" if dG_corrected_A < 0 else "UNFAVORABLE",
            })

            # Print 1800K values
            if abs(T - 1800) < 1:
                verdict = "FAVORABLE" if dG_corrected_A < 0 else "UNFAVORABLE"
                print("%-14s  %8.1f  %8.1f  %8.1f  %8.1f  %s" % (
                    product, dG_pure, cu_correction_kJ,
                    dG_corrected_A, dG_corrected_B, verdict))

    # Write CSV
    fieldnames = [
        "product", "T_K", "T_C", "dG_pure_kJ", "Cu_correction_kJ",
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
    # Plot: Pure vs Corrected comparison
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
        ax.text(1575, ax.get_ylim()[1] * 0.9, "Steelmaking\nrange",
                fontsize=8, color='#777777', ha='center', va='top', style='italic')
        ax.set_xlabel(r"Temperature ($^\circ$C)", fontsize=12)
        ax.set_ylabel(r"$\Delta G_{\mathrm{rxn}}$ (kJ/mol)", fontsize=12)
        ax.grid(True, which='major', alpha=0.3)
        ax.minorticks_on()
        ax.grid(True, which='minor', alpha=0.1)
        for spine in ax.spines.values():
            spine.set_visible(False)

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
    # Summary at 1800K
    # ==========================================================================
    print()
    print("=" * 70)
    print("RANKING AT 1800K — Activity-Corrected (a_Cu = %.4f)" % A_CU)
    print("=" * 70)
    print()

    results_1800 = [(r["product"], r["dG_pure_kJ"], r["dG_corrected_pO2_1atm_kJ"])
                    for r in out_rows if abs(r["T_K"] - 1800) < 1]
    results_1800.sort(key=lambda x: x[2])

    print("%-4s %-14s %10s %12s %10s" % (
        "Rank", "Product", "dG_pure", "dG_corrected", "Status"))
    print("-" * 55)
    for i, (product, dG_pure, dG_corr) in enumerate(results_1800, 1):
        status = "OK" if dG_corr < 0 else "LOST"
        print("%-4d %-14s %10.1f %12.1f %10s" % (
            i, product, dG_pure, dG_corr, status))

    n_surviving = sum(1 for _, _, dG in results_1800 if dG < 0)
    print()
    print("%d of %d reactions remain favorable after correction." % (
        n_surviving, len(results_1800)))
    print("=" * 70)


if __name__ == "__main__":
    main()
