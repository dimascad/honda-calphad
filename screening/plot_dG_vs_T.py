"""
Plot dG vs T for top 6 ternary reaction products.

Reads dG_vs_T_top6.csv (fine 25K resolution) and produces a
publication-quality figure showing reaction driving force vs temperature.

Colorblind-friendly palette per CLAUDE.md.

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "dG_vs_T_top6.csv"
# Also check against existing 50K data for verification
CSV_EXISTING = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "ternary_reaction_energies.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

# Product display order (most to least negative dG at 1800K)
PRODUCT_ORDER = [
    "CuFe2O4", "Cu3V2O8", "CuMn2O4", "Cu2SiO4", "CuB2O4", "CuAl2O4",
]

PRODUCT_LABELS = {
    "CuFe2O4": "CuFe$_2$O$_4$ (ferrite)",
    "Cu3V2O8": "Cu$_3$V$_2$O$_8$ (vanadate)",
    "CuMn2O4": "CuMn$_2$O$_4$ (manganite)",
    "Cu2SiO4": "Cu$_2$SiO$_4$ (orthosilicate)",
    "CuB2O4":  "CuB$_2$O$_4$ (borate)",
    "CuAl2O4": "CuAl$_2$O$_4$ (aluminate)",
}

# Colorblind palette extended (6 colors)
COLORS = {
    "CuFe2O4": "#0077BB",   # blue
    "Cu3V2O8": "#EE7733",   # orange
    "CuMn2O4": "#AA3377",   # purple
    "Cu2SiO4": "#009988",   # teal
    "CuB2O4":  "#EE3377",   # magenta
    "CuAl2O4": "#BBBBBB",   # gray
}

LINE_STYLES = {
    "CuFe2O4": "-",
    "Cu3V2O8": "--",
    "CuMn2O4": ":",
    "Cu2SiO4": "-.",
    "CuB2O4":  "-",
    "CuAl2O4": "--",
}

MARKERS = {
    "CuFe2O4": "o",
    "Cu3V2O8": "s",
    "CuMn2O4": "^",
    "Cu2SiO4": "D",
    "CuB2O4":  "v",
    "CuAl2O4": "P",
}


def load_csv(path):
    """Load CSV and return list of dicts."""
    with open(path) as f:
        return list(csv.DictReader(f))


def extract_dG_vs_T(rows, product):
    """Extract (T, dG) arrays for a given product."""
    T_vals = []
    dG_vals = []
    phases = []
    for r in rows:
        if r["product"] != product:
            continue
        try:
            T = float(r["T_K"])
            dG = float(r["dG_rxn_system_kJ"])
            T_vals.append(T)
            dG_vals.append(dG)
            phases.append(r.get("stable_phases", ""))
        except (ValueError, KeyError):
            pass
    return np.array(T_vals), np.array(dG_vals), phases


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run dG_vs_T_top6.py on OSU VM first.")
        return

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_csv(CSV_IN)

    # =================================================================
    # Verification against existing 50K data
    # =================================================================
    if CSV_EXISTING.exists():
        print("Verifying against existing ternary_reaction_energies.csv...")
        existing_rows = load_csv(CSV_EXISTING)
        max_diff = 0
        n_compared = 0
        for product in PRODUCT_ORDER:
            T_new, dG_new, _ = extract_dG_vs_T(rows, product)
            T_old, dG_old, _ = extract_dG_vs_T(existing_rows, product)
            if len(T_old) == 0:
                continue
            # Compare at overlapping temperatures (50K steps)
            for i, T in enumerate(T_old):
                matches = np.where(np.abs(T_new - T) < 5)[0]
                if len(matches) > 0:
                    diff = abs(dG_new[matches[0]] - dG_old[i])
                    max_diff = max(max_diff, diff)
                    n_compared += 1
        print(f"  Compared {n_compared} overlapping points")
        print(f"  Max deviation: {max_diff:.2f} kJ")
        if max_diff > 1.0:
            print("  WARNING: deviation > 1 kJ! Check data.")
        else:
            print("  PASS: all within 1 kJ tolerance")
        print()

    # =================================================================
    # Main plot: dG vs T
    # =================================================================
    fig, ax = plt.subplots(figsize=(10, 6))

    for product in PRODUCT_ORDER:
        T_arr, dG_arr, phases = extract_dG_vs_T(rows, product)
        if len(T_arr) == 0:
            continue

        # Sort by T
        order = np.argsort(T_arr)
        T_arr = T_arr[order]
        dG_arr = dG_arr[order]

        # Convert to Celsius for x-axis
        T_C = T_arr - 273.15

        ax.plot(T_C, dG_arr,
                color=COLORS[product],
                linestyle=LINE_STYLES[product],
                marker=MARKERS[product],
                markersize=4,
                markevery=3,  # don't crowd markers at 25K steps
                linewidth=1.8,
                label=PRODUCT_LABELS[product])

    # dG = 0 reference line
    ax.axhline(y=0, color='black', linewidth=0.8, linestyle='-', alpha=0.5)

    # Steelmaking temperature reference
    ax.axvline(x=1527, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.text(1530, ax.get_ylim()[0] * 0.05, "1527 C\n(steelmaking)",
            fontsize=8, color='gray', ha='left', va='bottom')

    ax.set_xlabel("Temperature (C)", fontsize=12)
    ax.set_ylabel(r"$\Delta G_{rxn}$ (kJ/mol)", fontsize=12)
    ax.set_title(r"Reaction Free Energy: Cu + MO$_x$ + O$_2$ $\rightarrow$ CuMO$_y$",
                 fontsize=13)

    # Gridlines per CLAUDE.md
    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)

    # Remove outer box
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(loc='upper left', fontsize=9, framealpha=0.9)

    plt.tight_layout()

    # Save
    png_path = FIG_DIR / "dG_vs_T_top6.png"
    pdf_path = FIG_DIR / "dG_vs_T_top6.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    fig.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)

    print(f"Figures saved:")
    print(f"  {png_path}")
    print(f"  {pdf_path}")

    # =================================================================
    # Phase transition detection
    # =================================================================
    print(f"\nPhase Transitions (where stable_phases change):")
    print("-" * 70)
    for product in PRODUCT_ORDER:
        T_arr, dG_arr, phases = extract_dG_vs_T(rows, product)
        if len(phases) < 2:
            continue
        order = np.argsort(T_arr)
        T_arr = T_arr[order]
        phases = [phases[i] for i in order]

        transitions = []
        for i in range(1, len(phases)):
            if phases[i] != phases[i-1]:
                transitions.append((T_arr[i], phases[i-1], phases[i]))

        if transitions:
            print(f"\n  {product}:")
            for T, before, after in transitions:
                print(f"    {T:.0f}K: {before} -> {after}")
        else:
            print(f"\n  {product}: no phase transitions detected")


if __name__ == "__main__":
    main()
