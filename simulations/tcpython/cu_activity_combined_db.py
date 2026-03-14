#!/usr/bin/env python3
"""
Measure Cu activity in METALLIC phase as oxide is added at 1800K.

This is the FIX for Script 2 (cu_activity_vs_oxide.py). The original used
TCOX14 alone, which has no metallic Cu phase (no FCC_A1). All Cu went into
IONIC_LIQ, giving flat a_Cu across all compositions.

This version loads TCFE + TCOX together, giving BOTH:
  - FCC_A1 / BCC_A2 / LIQUID (metallic phases from TCFE)
  - IONIC_LIQ / SPINEL / CORUNDUM (oxide phases from TCOX)

The result should show a_Cu in the metallic phase dropping as oxide is added,
which is the experimentally observable quantity.

PREREQUISITE: Run check_vm_capabilities.py first to confirm which TCFE version
is available. Edit THERMO_DB and KINETIC_DB below if needed.

Systems: Cu-Al-O, Cu-Mn-O, Cu-Fe-O, Cu-V-O
Fixed T=1800K, sweep X_Cu from 0.95 to 0.05 in 20 steps.

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cu_activity_combined_db.py
"""

import csv
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration — EDIT THESE based on check_vm_capabilities.py results
# =============================================================================
T_FIXED = 1800  # K (steelmaking temperature)

# Primary database (oxide thermodynamics)
OXIDE_DB = "TCOX14"

# Steel database (metallic phases) — check_vm_capabilities.py will tell you
# which is available. Try TCFE13 first, fall back to TCFE12, TCFE11, etc.
STEEL_DB = "TCFE13"  # <-- CHANGE THIS if check script says different

# X_Cu sweep
N_STEPS = 20
X_CU_VALUES = [0.95 - i * (0.95 - 0.05) / (N_STEPS - 1) for i in range(N_STEPS)]

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "cu_activity_combined_db.csv"

# Same oxide definitions as original Script 2
SYSTEMS = [
    {
        "name": "Cu-Al-O",
        "oxide": "Al2O3",
        "metal": "AL",
        "elements": ["CU", "AL", "O"],
        "metal_frac": 2/5,
        "O_frac": 3/5,
    },
    {
        "name": "Cu-Mn-O",
        "oxide": "MnO",
        "metal": "MN",
        "elements": ["CU", "MN", "O"],
        "metal_frac": 1/2,
        "O_frac": 1/2,
    },
    {
        "name": "Cu-Fe-O",
        "oxide": "FeO",
        "metal": "FE",
        "elements": ["CU", "FE", "O"],
        "metal_frac": 1/2,
        "O_frac": 1/2,
    },
    {
        "name": "Cu-V-O",
        "oxide": "V2O5",
        "metal": "V",
        "elements": ["CU", "V", "O"],
        "metal_frac": 2/7,
        "O_frac": 5/7,
    },
]


def try_databases(session, elements):
    """Try to load combined TCFE+TCOX. Fall back to TCOX-only if needed."""

    # Attempt 1: Combined databases
    db_pairs = [
        ("TCFE13", "TCOX14"),
        ("TCFE12", "TCOX14"),
        ("TCFE11", "TCOX13"),
        ("TCFE10", "TCOX12"),
    ]

    for steel_db, oxide_db in db_pairs:
        try:
            system = (session
                      .select_database_and_elements(steel_db, elements)
                      .without_default_phases()
                      .select_phase("*")
                      .get_system())

            # Check what phases are available
            phases = system.get_phase_names()
            has_fcc = any("FCC" in p for p in phases)
            has_ionic = any("IONIC" in p for p in phases)

            if has_fcc and has_ionic:
                print("  Loaded: %s + %s (FCC + IONIC_LIQ available)" % (steel_db, oxide_db))
                return system, "%s+%s" % (steel_db, oxide_db)
            elif has_fcc:
                print("  Loaded: %s (FCC available, no IONIC_LIQ)" % steel_db)
                return system, steel_db
            else:
                print("  Loaded: %s but missing FCC phase, trying next..." % steel_db)
                continue

        except Exception as e:
            err = str(e)[:80]
            print("  %s + %s failed: %s" % (steel_db, oxide_db, err))
            continue

    # Attempt 2: TCOX only (same as original Script 2)
    try:
        system = (session
                  .select_database_and_elements("TCOX14", elements)
                  .get_system())
        print("  WARNING: Falling back to TCOX14-only (no metallic phases)")
        return system, "TCOX14-only"
    except Exception as e:
        return None, "FAILED: %s" % str(e)[:60]


def main():
    print("=" * 70)
    print("TC-Python: Cu Activity (Combined DB) at {}K".format(T_FIXED))
    print("=" * 70)
    print("Strategy: Load TCFE + TCOX for metallic + oxide phases")
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

            # Try loading combined databases
            system, db_used = try_databases(session, sys_def["elements"])

            if system is None:
                print("  SYSTEM SETUP FAILED: %s" % db_used)
                for X_Cu in X_CU_VALUES:
                    all_rows.append({
                        "system": sys_name,
                        "oxide": oxide,
                        "database": db_used,
                        "T_K": T_FIXED,
                        "X_Cu": X_Cu,
                        "X_M": "",
                        "X_O": "",
                        "a_Cu": "",
                        "stable_phases": "ERROR: setup failed",
                        "notes": db_used,
                    })
                continue

            success = 0
            for X_Cu in X_CU_VALUES:
                row = {
                    "system": sys_name,
                    "oxide": oxide,
                    "database": db_used,
                    "T_K": T_FIXED,
                    "X_Cu": round(X_Cu, 6),
                }

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

                    # Flag if we got metallic phases
                    has_metal = any("FCC" in p or "BCC" in p or "LIQUID" in p
                                    for p in stable)
                    if has_metal:
                        row["notes"] = "metallic phase present"

                except Exception as e:
                    row["a_Cu"] = ""
                    row["stable_phases"] = "ERROR: {}".format(e)
                    row["notes"] = str(e)[:80]

                all_rows.append(row)

            print("  Completed: {}/{} compositions".format(success, N_STEPS))

            # Print summary
            sys_rows = [r for r in all_rows
                        if r["system"] == sys_name and r.get("a_Cu", "") != ""]
            if sys_rows:
                first = sys_rows[0]
                last = sys_rows[-1]
                print("  a_Cu at X_Cu={:.2f}: {}".format(
                    first["X_Cu"],
                    "{:.6f}".format(first["a_Cu"]) if isinstance(first["a_Cu"], float) else first["a_Cu"]))
                print("  a_Cu at X_Cu={:.2f}: {}".format(
                    last["X_Cu"],
                    "{:.6f}".format(last["a_Cu"]) if isinstance(last["a_Cu"], float) else last["a_Cu"]))
                # Check if values actually vary
                a_vals = [r["a_Cu"] for r in sys_rows if isinstance(r["a_Cu"], float)]
                if a_vals:
                    a_min = min(a_vals)
                    a_max = max(a_vals)
                    if abs(a_max - a_min) < 1e-6:
                        print("  WARNING: a_Cu is FLAT — still in invariant 2-phase field")
                    else:
                        print("  a_Cu range: {:.6f} to {:.6f} (variation: {:.2e})".format(
                            a_min, a_max, a_max - a_min))
            print()

    # Write CSV
    fieldnames = [
        "system", "oxide", "database", "T_K", "X_Cu", "X_M", "X_O",
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
    print("SUMMARY: Cu Activity at {} K (Combined DB)".format(T_FIXED))
    print("=" * 70)
    print("{:<12} {:>12} {:>12} {:>12} {:>8}".format(
        "System", "a_Cu(0.95)", "a_Cu(0.50)", "a_Cu(0.10)", "Varies?"))
    print("-" * 60)

    for sys_def in SYSTEMS:
        sys_name = sys_def["name"]
        sys_rows = [r for r in all_rows
                    if r["system"] == sys_name and r.get("a_Cu", "") != ""]
        vals = {}
        for r in sys_rows:
            for target in [0.95, 0.50, 0.10]:
                if abs(r["X_Cu"] - target) < 0.03:
                    vals[target] = r["a_Cu"]

        a_all = [r["a_Cu"] for r in sys_rows if isinstance(r["a_Cu"], float)]
        varies = "YES" if a_all and (max(a_all) - min(a_all)) > 1e-4 else "flat"

        line = "{:<12}".format(sys_name)
        for target in [0.95, 0.50, 0.10]:
            if target in vals and isinstance(vals[target], float):
                line += " {:>12.6f}".format(vals[target])
            else:
                line += " {:>12}".format("N/A")
        line += " {:>8}".format(varies)
        print(line)

    print("=" * 70)


if __name__ == "__main__":
    main()
