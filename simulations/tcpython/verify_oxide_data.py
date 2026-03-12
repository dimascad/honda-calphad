#!/usr/bin/env python3
"""
Verify TC-Python oxide Gibbs energy results against literature values.

Literature reference values (dG_f per mol O2, in kJ) at 1000 K (~727 C):
Sources: Ellingham diagram standard references (Gaskell, Kubaschewski)

Run this AFTER extract_oxide_gibbs.py to check that results are reasonable.
"""

import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "tcpython" / "raw" / "oxide_gibbs_energies.csv"

# Literature dG_f values at ~1000 K (kJ/mol O2) from standard Ellingham data
# Negative = exothermic formation (all oxides form spontaneously from elements)
LITERATURE_1000K = {
    # Original 7 (already verified by Zhang)
    "Cu2O":  -191,   # least stable
    "CuO":   -132,   # even less stable than Cu2O per O2
    "Al2O3": -908,   # very stable
    "MgO":   -987,   # most stable of the set
    "SiO2":  -730,   # moderately stable
    "TiO2":  -760,   # moderately stable
    "FeO":   -411,   # moderately stable
    # Screening expansion (Feb 2026)
    "CaO":   -1060,  # extremely stable, near MgO
    "ZrO2":  -920,   # very stable, between Al2O3 and MgO
    "Cr2O3": -580,   # moderate
    "MnO":   -640,   # moderate, between FeO and SiO2
    # Moonshot oxides (Mar 2026) — literature values from EMF data & NIST
    "NiO":   -244,   # just above Cu2O — Ni is a co-tramp element
    "CoO":   -430,   # between FeO and MnO
    "PbO":   -239,   # near Cu2O — Pb is a co-tramp element
    "B2O3":  -845,   # low-melting flux, Cu2O soluble in borate slag
    "V2O5":  -542,   # experimental evidence for Cu removal via copper vanadates
    "La2O3": -1148,  # most stable — rare earth anchor
    "CeO2":  -1000,  # Ce4+/Ce3+ redox active oxygen carrier
}

# Acceptable tolerance: 15% of literature value (TC databases may differ slightly)
TOLERANCE = 0.15


def main():
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Run extract_oxide_gibbs.py first!")
        return

    # Read CSV
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Find row closest to 1000 K
    row_1000 = None
    for row in rows:
        if abs(float(row["T_K"]) - 1000) < 5:
            row_1000 = row
            break

    if not row_1000:
        print("ERROR: No data at ~1000 K in CSV")
        return

    print("=" * 75)
    print("VERIFICATION: TC-Python vs Literature at 1000 K")
    print("=" * 75)
    print(f"\n{'Oxide':<10} {'TC-Python':>14} {'Literature':>14} {'Diff':>10} {'Status':>10}")
    print("-" * 65)

    all_pass = True
    missing = []

    for oxide, lit_val in LITERATURE_1000K.items():
        col = f"dG_{oxide}_per_O2"
        if col not in row_1000 or not row_1000[col]:
            missing.append(oxide)
            print(f"{oxide:<10} {'MISSING':>14} {lit_val:>+12.0f} kJ {'---':>10} {'MISSING':>10}")
            continue

        tc_val = float(row_1000[col]) / 1000  # J -> kJ
        diff_pct = abs(tc_val - lit_val) / abs(lit_val) * 100
        status = "OK" if diff_pct < TOLERANCE * 100 else "CHECK"
        if status == "CHECK":
            all_pass = False

        print(f"{oxide:<10} {tc_val:>+12.1f} kJ {lit_val:>+12.0f} kJ {diff_pct:>8.1f}% {status:>10}")

    print("-" * 65)

    if missing:
        print(f"\nMISSING OXIDES: {', '.join(missing)}")
        print("These need to be extracted — run extract_oxide_gibbs.py on the OSU VM.")

    if all_pass and not missing:
        print("\nAll values within 15% of literature. Results look good.")
    elif not all_pass:
        print("\nSome values outside 15% tolerance — review flagged entries.")
        print("Small deviations are expected (different databases, activity models).")
        print("Large deviations (>25%) suggest wrong phase or stoichiometry.")

    # Additional check: ordering should match Ellingham diagram
    print(f"\n{'='*75}")
    print("STABILITY ORDERING CHECK (most stable -> least stable at 1000 K)")
    print("Expected: La2O3 > CaO > CeO2 > MgO > ZrO2 > Al2O3 > B2O3 > TiO2 > SiO2 > MnO > V2O5 > Cr2O3 > CoO > FeO > NiO > PbO > Cu2O > CuO")
    print("=" * 75)

    found = {}
    for oxide in LITERATURE_1000K:
        col = f"dG_{oxide}_per_O2"
        if col in row_1000 and row_1000[col]:
            found[oxide] = float(row_1000[col])

    if found:
        sorted_oxides = sorted(found.items(), key=lambda x: x[1])
        print("\nTC-Python ordering (most negative = most stable):")
        for i, (name, val) in enumerate(sorted_oxides, 1):
            print(f"  {i:>2}. {name:<10} {val/1000:>+10.1f} kJ/mol O2")

    # Check for phase issues
    print(f"\n{'='*75}")
    print("PHASE IDENTIFICATION CHECK")
    print("=" * 75)

    phase_cols = {oxide: f"oxide_phase_{oxide}" for oxide in LITERATURE_1000K}
    for oxide, col in phase_cols.items():
        if col in row_1000:
            phase = row_1000[col]
            flag = " *** NOT_FOUND — used system GM instead" if phase == "NOT_FOUND" else ""
            print(f"  {oxide:<10} phase: {phase:<20}{flag}")
        else:
            print(f"  {oxide:<10} NOT IN CSV")


if __name__ == "__main__":
    main()
