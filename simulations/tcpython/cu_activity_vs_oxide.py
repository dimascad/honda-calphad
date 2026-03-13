#!/usr/bin/env python3
"""
Measure Cu activity drop as oxide is added to Cu melt at 1800K.

This is the key experimental observable: if an oxide captures Cu, the
activity of Cu in the melt should decrease. A steeper a_Cu drop means
stronger Cu-oxide interaction.

Systems: Cu-Al-O, Cu-Mn-O, Cu-Fe-O, Cu-V-O
Fixed T=1800K, sweep X_Cu from 0.90 to 0.05 in 20 steps.
The non-Cu fraction maintains the oxide's stoichiometric ratio:
  - Al2O3: X_Al:X_O = 2:3
  - MnO:   X_Mn:X_O = 1:1
  - FeO:   X_Fe:X_O = 1:1
  - V2O5:  X_V:X_O  = 2:5

Key API: result.get_value_of("AC(CU)") for Cu activity.

Output: ../../data/tcpython/raw/cu_activity_vs_oxide.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cu_activity_vs_oxide.py
"""

import csv
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_FIXED = 1800  # K (steelmaking temperature)
DATABASE = "TCOX14"

# X_Cu sweep: 0.90 down to 0.05 in 20 steps
N_STEPS = 20
X_CU_VALUES = [0.90 - i * (0.90 - 0.05) / (N_STEPS - 1) for i in range(N_STEPS)]

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "cu_activity_vs_oxide.csv"

# Oxide definitions: element, TC symbol, O ratio in non-Cu fraction
# For Cu-M-O at a given X_Cu:
#   X_oxide_total = 1 - X_Cu
#   X_M = X_oxide_total * (metal_atoms / total_oxide_atoms)
#   X_O = X_oxide_total * (oxygen_atoms / total_oxide_atoms)
SYSTEMS = [
    {
        "name": "Cu-Al-O",
        "oxide": "Al2O3",
        "metal": "AL",
        "elements": ["CU", "AL", "O"],
        # Al2O3: 2 Al + 3 O = 5 atoms -> metal_frac = 2/5, O_frac = 3/5
        "metal_frac": 2/5,
        "O_frac": 3/5,
    },
    {
        "name": "Cu-Mn-O",
        "oxide": "MnO",
        "metal": "MN",
        "elements": ["CU", "MN", "O"],
        # MnO: 1 Mn + 1 O = 2 atoms -> metal_frac = 1/2, O_frac = 1/2
        "metal_frac": 1/2,
        "O_frac": 1/2,
    },
    {
        "name": "Cu-Fe-O",
        "oxide": "FeO",
        "metal": "FE",
        "elements": ["CU", "FE", "O"],
        # FeO: 1 Fe + 1 O = 2 atoms
        "metal_frac": 1/2,
        "O_frac": 1/2,
    },
    {
        "name": "Cu-V-O",
        "oxide": "V2O5",
        "metal": "V",
        "elements": ["CU", "V", "O"],
        # V2O5: 2 V + 5 O = 7 atoms -> metal_frac = 2/7, O_frac = 5/7
        "metal_frac": 2/7,
        "O_frac": 5/7,
    },
]


def main():
    print("=" * 70)
    print("TC-Python: Cu Activity vs Oxide Addition at {}K".format(T_FIXED))
    print("=" * 70)
    print("Database: {}".format(DATABASE))
    print("X_Cu range: {:.2f} to {:.2f} ({} steps)".format(
        X_CU_VALUES[0], X_CU_VALUES[-1], N_STEPS))
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
            metal = sys_def["metal"]
            oxide = sys_def["oxide"]
            metal_frac = sys_def["metal_frac"]
            O_frac = sys_def["O_frac"]

            print("=" * 60)
            print("System: {} (oxide = {})".format(sys_name, oxide))
            print("=" * 60)

            try:
                system = (session
                          .select_database_and_elements(DATABASE, sys_def["elements"])
                          .get_system())
            except Exception as e:
                print("  SYSTEM SETUP ERROR: {}".format(e))
                for X_Cu in X_CU_VALUES:
                    all_rows.append({
                        "system": sys_name,
                        "oxide": oxide,
                        "T_K": T_FIXED,
                        "X_Cu": X_Cu,
                        "X_M": "",
                        "X_O": "",
                        "a_Cu": "",
                        "stable_phases": "ERROR: {}".format(e),
                        "notes": "System setup failed",
                    })
                continue

            success = 0
            for X_Cu in X_CU_VALUES:
                row = {
                    "system": sys_name,
                    "oxide": oxide,
                    "T_K": T_FIXED,
                    "X_Cu": round(X_Cu, 6),
                }

                # Non-Cu fraction distributed in oxide stoichiometry
                X_oxide_total = 1.0 - X_Cu
                X_M = X_oxide_total * metal_frac
                X_O = X_oxide_total * O_frac
                row["X_M"] = round(X_M, 6)
                row["X_O"] = round(X_O, 6)

                try:
                    calc = system.with_single_equilibrium_calculation()
                    calc.set_condition(ThermodynamicQuantity.temperature(), T_FIXED)
                    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                        X_Cu
                    )
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                        X_O
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

            print("  Completed: {}/{} compositions".format(success, N_STEPS))

            # Print a few key values
            sys_rows = [r for r in all_rows
                        if r["system"] == sys_name and r.get("a_Cu", "") != ""]
            if sys_rows:
                first = sys_rows[0]
                last = sys_rows[-1]
                print("  a_Cu at X_Cu={:.2f}: {:.4f}".format(
                    first["X_Cu"], first["a_Cu"]))
                print("  a_Cu at X_Cu={:.2f}: {:.4f}".format(
                    last["X_Cu"], last["a_Cu"]))
            print()

    # =========================================================================
    # Write CSV
    # =========================================================================
    fieldnames = [
        "system", "oxide", "T_K", "X_Cu", "X_M", "X_O",
        "a_Cu", "stable_phases", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("=" * 70)
    print("CSV written to: {}".format(OUTPUT_FILE))
    print("{} rows ({} systems x {} compositions)".format(
        len(all_rows), len(SYSTEMS), N_STEPS))
    print("Finished: {}".format(datetime.now().isoformat()))
    print("=" * 70)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY: Cu Activity at 1800K")
    print("=" * 70)
    print("{:<12} {:>10} {:>10} {:>10}".format(
        "System", "a_Cu(0.90)", "a_Cu(0.50)", "a_Cu(0.10)"))
    print("-" * 46)

    for sys_def in SYSTEMS:
        sys_name = sys_def["name"]
        sys_rows = [r for r in all_rows
                    if r["system"] == sys_name and r.get("a_Cu", "") != ""]
        vals = {}
        for r in sys_rows:
            for target in [0.90, 0.50, 0.10]:
                if abs(r["X_Cu"] - target) < 0.03:
                    vals[target] = r["a_Cu"]
        line = "{:<12}".format(sys_name)
        for target in [0.90, 0.50, 0.10]:
            if target in vals:
                line += " {:>10.4f}".format(vals[target])
            else:
                line += " {:>10}".format("N/A")
        print(line)

    print("=" * 70)


if __name__ == "__main__":
    main()
