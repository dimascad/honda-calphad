"""
Decompose CuFe2O4 reaction energy into Cu-capture vs Fe-oxidation components.

Reads cufe2o4_alternative_reaction.csv and computes:
  - Alternative dG (Fe2O3 pathway): pure Cu-capture energy
  - Original dG (FeO pathway): Cu-capture + Fe-oxidation energy
  - Difference: Fe-oxidation contribution

If the alternative dG is still strongly negative, Cu capture alone
is a significant driving force. If near zero, most of the original
-112 kJ came from Fe2+ -> Fe3+ oxidation.

Run locally after copying CSV from OSU VM.
"""

import csv
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "cufe2o4_alternative_reaction.csv"
CSV_OUT = SCRIPT_DIR / "cufe2o4_decomposition_results.csv"


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run cufe2o4_alternative_reaction.py on OSU VM first.")
        return

    with open(CSV_IN) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("=" * 75)
    print("CuFe2O4 Reaction Energy Decomposition")
    print("=" * 75)
    print()
    print("Original:    Cu + 2FeO  + O2     -> CuFe2O4  (Fe2+ -> Fe3+ + Cu capture)")
    print("Alternative: Cu + Fe2O3 + 0.5 O2 -> CuFe2O4  (Cu capture only)")
    print("Difference:  Energy from Fe2+ -> Fe3+ oxidation")
    print()

    # Parse data
    T_arr = []
    dG_alt = []
    dG_orig = []
    dG_fe_ox = []

    for r in rows:
        try:
            T = float(r["T_K"])
            alt = float(r["dG_alternative_kJ"])
            orig = float(r["dG_original_kJ"])
            fe = float(r["dG_Fe_oxidation_kJ"])
            T_arr.append(T)
            dG_alt.append(alt)
            dG_orig.append(orig)
            dG_fe_ox.append(fe)
        except (ValueError, KeyError):
            pass

    T_arr = np.array(T_arr)
    dG_alt = np.array(dG_alt)
    dG_orig = np.array(dG_orig)
    dG_fe_ox = np.array(dG_fe_ox)

    if len(T_arr) == 0:
        print("ERROR: No valid data found in CSV.")
        return

    # Print table
    print(f"{'T (K)':<8} {'T (C)':<8} {'Alt dG':>10} {'Orig dG':>10} {'Fe-ox':>10} {'Cu-capture %':>14}")
    print("-" * 64)

    out_rows = []
    for i in range(len(T_arr)):
        T = T_arr[i]
        T_C = T - 273.15
        alt = dG_alt[i]
        orig = dG_orig[i]
        fe = dG_fe_ox[i]

        # Percentage of original dG that is Cu-capture (alternative)
        if abs(orig) > 0.1:
            cu_pct = 100.0 * alt / orig
        else:
            cu_pct = 0.0

        print(f"{T:<8.0f} {T_C:<8.1f} {alt:>+10.1f} {orig:>+10.1f} {fe:>10.1f} {cu_pct:>13.1f}%")

        out_rows.append({
            "T_K": T,
            "T_C": T_C,
            "dG_alternative_kJ": alt,
            "dG_original_kJ": orig,
            "dG_Fe_oxidation_kJ": fe,
            "Cu_capture_pct": round(cu_pct, 1),
        })

    # Summary at key temperatures
    print()
    print("=" * 75)
    print("KEY TEMPERATURES")
    print("=" * 75)

    for T_target in [1000, 1500, 1800]:
        idx = int(np.argmin(np.abs(T_arr - T_target)))
        if np.abs(T_arr[idx] - T_target) < 30:
            alt = dG_alt[idx]
            orig = dG_orig[idx]
            fe = dG_fe_ox[idx]
            cu_pct = 100.0 * alt / orig if abs(orig) > 0.1 else 0
            print(f"\n  At {T_arr[idx]:.0f}K ({T_arr[idx]-273.15:.0f}C):")
            print(f"    Original dG (FeO):      {orig:+.1f} kJ/mol")
            print(f"    Alternative dG (Fe2O3): {alt:+.1f} kJ/mol")
            print(f"    Fe-oxidation component: {fe:.1f} kJ/mol")
            print(f"    Cu-capture fraction:    {cu_pct:.0f}% of total driving force")

    # Interpretation
    print()
    print("=" * 75)
    print("INTERPRETATION")
    print("=" * 75)

    idx_1800 = int(np.argmin(np.abs(T_arr - 1800)))
    if np.abs(T_arr[idx_1800] - 1800) < 30:
        alt_1800 = dG_alt[idx_1800]
        orig_1800 = dG_orig[idx_1800]
        fe_1800 = dG_fe_ox[idx_1800]

        if alt_1800 < -10:
            print(f"  Cu capture alone provides {alt_1800:+.1f} kJ driving force.")
            print("  This is STRONG: Cu-capture is independently favorable,")
            print("  even without the Fe-oxidation bonus.")
        elif alt_1800 < 0:
            print(f"  Cu capture alone provides {alt_1800:+.1f} kJ driving force.")
            print("  MARGINAL: Cu capture works but Fe-oxidation is the main driver.")
        else:
            print(f"  Cu capture alone gives {alt_1800:+.1f} kJ (UNFAVORABLE).")
            print("  The original -112 kJ is almost entirely from Fe2+ -> Fe3+ oxidation.")
            print("  CuFe2O4 formation is driven by Fe chemistry, not Cu affinity.")

        print(f"\n  Comparison to CuAl2O4 (-32 kJ): ", end="")
        if abs(alt_1800 - (-32)) < 15:
            print("similar magnitude, consistent with pure Cu-capture mechanism.")
        elif alt_1800 < -32:
            print("stronger than CuAl2O4, Cu-Fe-O has extra affinity.")
        else:
            print("weaker than CuAl2O4 after removing Fe-oxidation.")

    # Write CSV
    if out_rows:
        fieldnames = list(out_rows[0].keys())
        with open(CSV_OUT, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"\nCSV written to: {CSV_OUT}")


if __name__ == "__main__":
    main()
