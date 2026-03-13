#!/usr/bin/env python3
"""
Test whether slag basicity affects Cu capture.

Quaternary systems: Cu-Mn-Si-O, Cu-Al-Si-O
Fix X_Cu = 0.003 (steelmaking Cu level ~0.3 wt%), vary the ratio
of basic oxide (MnO or Al2O3) to acidic oxide (SiO2).

For Cu-Mn-Si-O:
  Vary MnO:SiO2 ratio from 0.2 to 3.0 (basic to very basic slag)
  At each ratio, set X_Mn, X_Si, X_O to maintain stoichiometry.

For Cu-Al-Si-O:
  Vary Al2O3:SiO2 ratio from 0.2 to 3.0
  At each ratio, set X_Al, X_Si, X_O to maintain stoichiometry.

Record a_Cu and stable phases at each basicity.
If a_Cu decreases with basicity, basic slag promotes Cu capture.

T = 1800K (steelmaking), P = 101325 Pa.

Output: ../../data/tcpython/raw/slag_composition_effects.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" slag_composition_effects.py
"""

import csv
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_FIXED = 1800  # K
DATABASE = "TCOX14"
X_CU_FIXED = 0.003  # ~0.3 wt% Cu in steel

N_STEPS = 15
# Basicity ratio (basic_oxide : SiO2) from 0.2 to 3.0
RATIO_MIN = 0.2
RATIO_MAX = 3.0
RATIOS = [RATIO_MIN + i * (RATIO_MAX - RATIO_MIN) / (N_STEPS - 1)
          for i in range(N_STEPS)]

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "slag_composition_effects.csv"

# =============================================================================
# System definitions
#
# For Cu-Mn-Si-O with ratio R = MnO:SiO2 (in formula units):
#   R formula units MnO  = R Mn + R O atoms
#   1 formula unit SiO2 = 1 Si + 2 O atoms
#   Total non-Cu atoms = R + R + 1 + 2 = 2R + 3
#   X_Mn = R / (2R + 3), X_Si = 1 / (2R + 3), X_O = (R + 2) / (2R + 3)
#   Then scale by (1 - X_Cu) and add X_Cu.
#
# For Cu-Al-Si-O with ratio R = Al2O3:SiO2 (in formula units):
#   R formula units Al2O3 = 2R Al + 3R O atoms
#   1 formula unit SiO2 = 1 Si + 2 O atoms
#   Total non-Cu atoms = 2R + 3R + 1 + 2 = 5R + 3
#   X_Al = 2R / (5R + 3), X_Si = 1 / (5R + 3), X_O = (3R + 2) / (5R + 3)
# =============================================================================

SYSTEMS = [
    {
        "name": "Cu-Mn-Si-O",
        "elements": ["CU", "MN", "SI", "O"],
        "basic_oxide": "MnO",
        "ratio_label": "MnO:SiO2",
        # Given ratio R, compute non-Cu mole fractions
        # (before scaling by 1 - X_Cu)
        "calc_fracs": lambda R: {
            "MN": R / (2*R + 3),
            "SI": 1 / (2*R + 3),
            "O":  (R + 2) / (2*R + 3),
        },
        # For TC: set 3 conditions (CU, MN, O), SI fills remainder
        "set_conditions": ["CU", "MN", "O"],
    },
    {
        "name": "Cu-Al-Si-O",
        "elements": ["CU", "AL", "SI", "O"],
        "basic_oxide": "Al2O3",
        "ratio_label": "Al2O3:SiO2",
        "calc_fracs": lambda R: {
            "AL": 2*R / (5*R + 3),
            "SI": 1 / (5*R + 3),
            "O":  (3*R + 2) / (5*R + 3),
        },
        # For TC: set 3 conditions (CU, AL, O), SI fills remainder
        "set_conditions": ["CU", "AL", "O"],
    },
]


def main():
    print("=" * 70)
    print("TC-Python: Slag Composition Effects on Cu Activity at {}K".format(T_FIXED))
    print("=" * 70)
    print("Database: {}".format(DATABASE))
    print("X_Cu fixed: {}".format(X_CU_FIXED))
    print("Basicity ratios: {:.1f} to {:.1f} ({} steps)".format(
        RATIO_MIN, RATIO_MAX, N_STEPS))
    print("Systems: {}".format(", ".join(s["name"] for s in SYSTEMS)))
    print("Output: {}".format(OUTPUT_FILE))
    print("Started: {}".format(datetime.now().isoformat()))
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        for sys_def in SYSTEMS:
            sys_name = sys_def["name"]
            ratio_label = sys_def["ratio_label"]

            print("=" * 60)
            print("System: {} (ratio = {})".format(sys_name, ratio_label))
            print("=" * 60)

            try:
                system = (session
                          .select_database_and_elements(DATABASE, sys_def["elements"])
                          .get_system())
            except Exception as e:
                print("  SYSTEM SETUP ERROR: {}".format(e))
                for R in RATIOS:
                    all_rows.append({
                        "system": sys_name,
                        "ratio_label": ratio_label,
                        "ratio_value": round(R, 4),
                        "T_K": T_FIXED,
                        "X_Cu": X_CU_FIXED,
                        "X_M1": "", "X_Si": "", "X_O": "",
                        "a_Cu": "",
                        "stable_phases": "ERROR: {}".format(e),
                        "notes": "System setup failed",
                    })
                continue

            success = 0
            for R in RATIOS:
                # Compute slag oxide fractions (non-Cu portion)
                slag_fracs = sys_def["calc_fracs"](R)

                # Scale to total composition
                scale = 1.0 - X_CU_FIXED
                X_Cu = X_CU_FIXED

                # Element fractions after scaling
                comp = {}
                for el, frac in slag_fracs.items():
                    comp[el] = frac * scale

                # Get the metal (non-Si, non-O) fraction for display
                metal_els = [el for el in slag_fracs if el not in ("SI", "O")]
                X_M1 = comp.get(metal_els[0], 0) if metal_els else 0
                X_Si = comp.get("SI", 0)
                X_O = comp.get("O", 0)

                row = {
                    "system": sys_name,
                    "ratio_label": ratio_label,
                    "ratio_value": round(R, 4),
                    "T_K": T_FIXED,
                    "X_Cu": X_CU_FIXED,
                    "X_M1": round(X_M1, 6),
                    "X_Si": round(X_Si, 6),
                    "X_O": round(X_O, 6),
                }

                try:
                    calc = system.with_single_equilibrium_calculation()
                    calc.set_condition(ThermodynamicQuantity.temperature(), T_FIXED)
                    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)

                    # Set 3 mole fraction conditions; 4th element (SI) fills remainder
                    cond_els = sys_def["set_conditions"]
                    for el in cond_els:
                        val = X_Cu if el == "CU" else comp[el]
                        calc.set_condition(
                            ThermodynamicQuantity.mole_fraction_of_a_component(el),
                            val
                        )

                    result = calc.calculate()

                    a_Cu = result.get_value_of("AC(CU)")
                    stable = result.get_stable_phases()

                    row["a_Cu"] = a_Cu
                    row["stable_phases"] = "; ".join(stable)
                    row["notes"] = ""
                    success += 1

                except Exception as e:
                    row["a_Cu"] = ""
                    row["stable_phases"] = "ERROR: {}".format(e)
                    row["notes"] = str(e)

                all_rows.append(row)

            print("  Completed: {}/{} ratios".format(success, N_STEPS))

            # Print key values
            sys_rows = [r for r in all_rows
                        if r["system"] == sys_name and r.get("a_Cu", "") != ""]
            if sys_rows:
                first = sys_rows[0]
                last = sys_rows[-1]
                print("  a_Cu at R={:.1f}: {:.6f}".format(
                    first["ratio_value"], first["a_Cu"]))
                print("  a_Cu at R={:.1f}: {:.6f}".format(
                    last["ratio_value"], last["a_Cu"]))

                # Check monotonicity
                a_vals = [r["a_Cu"] for r in sys_rows]
                diffs = [a_vals[i+1] - a_vals[i] for i in range(len(a_vals)-1)]
                if all(d <= 0 for d in diffs):
                    print("  Trend: monotonically decreasing (more basic = lower a_Cu)")
                elif all(d >= 0 for d in diffs):
                    print("  Trend: monotonically increasing (more basic = higher a_Cu)")
                else:
                    print("  Trend: non-monotonic")
            print()

    # =========================================================================
    # Write CSV
    # =========================================================================
    fieldnames = [
        "system", "ratio_label", "ratio_value", "T_K",
        "X_Cu", "X_M1", "X_Si", "X_O",
        "a_Cu", "stable_phases", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 70)
    print("CSV written to: {}".format(OUTPUT_FILE))
    print("{} rows ({} systems x {} ratios)".format(
        len(all_rows), len(SYSTEMS), N_STEPS))
    print("Finished: {}".format(datetime.now().isoformat()))
    print("=" * 70)


if __name__ == "__main__":
    main()
