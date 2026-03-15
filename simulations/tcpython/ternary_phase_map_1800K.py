#!/usr/bin/env python3
"""
Map phase regions across Cu-M-O composition space at 1800K.

Systems: Cu-Al-O, Cu-Mn-O (optionally Cu-Fe-O)
Fixed T=1800K, 20x20 grid:
  X_Cu in [0.01, 0.50] (20 steps)
  X_O  in [0.01, 0.70] (20 steps)
  X_M  = 1 - X_Cu - X_O (skip if X_M <= 0.01)

This maps which equilibrium phases are stable across the ternary
composition space at steelmaking temperature. Expect IONIC_LIQ to
dominate at 1800K (consistent with existing finding that all ternary
phases melt).

~270 valid points per system, ~540-810 total. Longest script (~15-35 min).

Output: ../../data/tcpython/raw/ternary_phase_map_1800K.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" ternary_phase_map_1800K.py
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

# Composition grid
N_GRID = 20
X_CU_MIN, X_CU_MAX = 0.01, 0.50
X_O_MIN, X_O_MAX = 0.01, 0.70
X_M_MIN = 0.01  # skip points where metal fraction is too low

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "ternary_phase_map_1800K.csv"

SYSTEMS = [
    {"name": "Cu-Al-O", "metal": "AL", "elements": ["CU", "AL", "O"]},
    {"name": "Cu-Mn-O", "metal": "MN", "elements": ["CU", "MN", "O"]},
    {"name": "Cu-Fe-O", "metal": "FE", "elements": ["CU", "FE", "O"]},
    {"name": "Cu-V-O",  "metal": "V",  "elements": ["CU", "V", "O"]},
    {"name": "Cu-Si-O", "metal": "SI", "elements": ["CU", "SI", "O"]},
]


def main():
    print("=" * 70)
    print("TC-Python: Ternary Phase Map at {}K".format(T_FIXED))
    print("=" * 70)
    print("Database: {}".format(DATABASE))
    print("Grid: {}x{} (X_Cu: {}-{}, X_O: {}-{})".format(
        N_GRID, N_GRID, X_CU_MIN, X_CU_MAX, X_O_MIN, X_O_MAX))
    print("Systems: {}".format(", ".join(s["name"] for s in SYSTEMS)))
    print("Output: {}".format(OUTPUT_FILE))
    print("Started: {}".format(datetime.now().isoformat()))
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build composition grid
    X_Cu_vals = [X_CU_MIN + i * (X_CU_MAX - X_CU_MIN) / (N_GRID - 1)
                 for i in range(N_GRID)]
    X_O_vals = [X_O_MIN + i * (X_O_MAX - X_O_MIN) / (N_GRID - 1)
                for i in range(N_GRID)]

    # Count valid points
    valid_points = []
    for X_Cu in X_Cu_vals:
        for X_O in X_O_vals:
            X_M = 1.0 - X_Cu - X_O
            if X_M > X_M_MIN:
                valid_points.append((X_Cu, X_O, X_M))

    print("Valid grid points per system: {}".format(len(valid_points)))
    print("Total calculations: ~{}".format(len(valid_points) * len(SYSTEMS)))
    print()

    all_rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        for sys_def in SYSTEMS:
            sys_name = sys_def["name"]
            metal = sys_def["metal"]

            print("=" * 60)
            print("System: {}".format(sys_name))
            print("=" * 60)

            try:
                system = (session
                          .select_database_and_elements(DATABASE, sys_def["elements"])
                          .get_system())
            except Exception as e:
                print("  SYSTEM SETUP ERROR: {}".format(e))
                for X_Cu, X_O, X_M in valid_points:
                    all_rows.append({
                        "system": sys_name,
                        "T_K": T_FIXED,
                        "X_Cu": round(X_Cu, 6),
                        "X_M": round(X_M, 6),
                        "X_O": round(X_O, 6),
                        "stable_phases": "ERROR: {}".format(e),
                        "num_phases": "",
                        "dominant_phase": "",
                        "GM_system": "",
                        "notes": "System setup failed",
                    })
                continue

            success = 0
            total = len(valid_points)
            for idx, (X_Cu, X_O, X_M) in enumerate(valid_points):
                row = {
                    "system": sys_name,
                    "T_K": T_FIXED,
                    "X_Cu": round(X_Cu, 6),
                    "X_M": round(X_M, 6),
                    "X_O": round(X_O, 6),
                }

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

                    stable = result.get_stable_phases()
                    GM_system = result.get_value_of("GM")

                    # Dominant phase: first in list (TC returns by fraction)
                    dominant = stable[0] if stable else ""

                    row["stable_phases"] = "; ".join(stable)
                    row["num_phases"] = len(stable)
                    row["dominant_phase"] = dominant
                    row["GM_system"] = GM_system
                    row["notes"] = ""
                    success += 1

                except Exception as e:
                    row["stable_phases"] = "ERROR: {}".format(e)
                    row["num_phases"] = ""
                    row["dominant_phase"] = ""
                    row["GM_system"] = ""
                    row["notes"] = str(e)

                all_rows.append(row)

                # Progress every 50 points
                if (idx + 1) % 50 == 0 or idx == total - 1:
                    print("  {}: {}/{} ({} OK)".format(
                        sys_name, idx + 1, total, success))

            print("  Completed: {}/{} compositions\n".format(success, total))

            # Phase frequency summary
            phase_counts = {}
            sys_rows = [r for r in all_rows
                        if r["system"] == sys_name and r.get("dominant_phase", "")]
            for r in sys_rows:
                p = r["dominant_phase"]
                phase_counts[p] = phase_counts.get(p, 0) + 1

            if phase_counts:
                print("  Phase frequency (dominant):")
                for phase, count in sorted(phase_counts.items(),
                                           key=lambda x: -x[1]):
                    pct = 100.0 * count / len(sys_rows)
                    print("    {:<20} {:>4} ({:.0f}%)".format(phase, count, pct))

    # =========================================================================
    # Write CSV
    # =========================================================================
    fieldnames = [
        "system", "T_K", "X_Cu", "X_M", "X_O",
        "stable_phases", "num_phases", "dominant_phase",
        "GM_system", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\n" + "=" * 70)
    print("CSV written to: {}".format(OUTPUT_FILE))
    print("{} rows ({} systems)".format(len(all_rows), len(SYSTEMS)))
    print("Finished: {}".format(datetime.now().isoformat()))
    print("=" * 70)


if __name__ == "__main__":
    main()
