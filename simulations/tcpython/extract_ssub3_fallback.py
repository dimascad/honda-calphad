#!/usr/bin/env python3
"""
Fallback extraction for oxides NOT in TCOX14.

Uses SSUB3 (pure substance database) to get Gibbs energies for:
  - PbO  (Pb not in TCOX14)
  - B2O3 (B in TCOX14 but phase not found)
  - CeO2 (Ce not in TCOX14)

Run on OSU VM:
  "C:\Program Files\Thermo-Calc\2025b\python\python.exe" extract_ssub3_fallback.py

This appends columns to the existing oxide_gibbs_energies.csv.
"""

import csv
import os
from pathlib import Path

try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not found. Run this on the OSU VM.")
    exit(1)

# Output CSV path (same as main extraction)
CSV_PATH = Path(__file__).parent.parent.parent / "data" / "tcpython" / "raw" / "oxide_gibbs_energies.csv"

# Temperature range (must match main extraction: 500-2000K, step 50)
T_START = 500
T_END = 2000
T_STEP = 50
TEMPS = list(range(T_START, T_END + 1, T_STEP))

# Oxides to extract from SSUB3
# SSUB3 uses stoichiometric compound names, not element systems
FALLBACK_OXIDES = {
    "PbO": {
        "elements": ["PB", "O"],
        "X_O": 0.500,          # PbO: 1 Pb + 1 O = 50% O
        "atoms_per_formula": 2,
        "metal_per_O2": 2,     # 2 PbO per mol O2
        "oxide_per_O2": 2,
        "phase_patterns": ["LITHARGE", "PBO", "MASSICOT", "PB_MONOXIDE"],
    },
    "B2O3": {
        "elements": ["B", "O"],
        "X_O": 0.600,          # B2O3: 2B + 3O / 5 atoms = 60% O
        "atoms_per_formula": 5,
        "metal_per_O2": 4/3,   # (4/3) B2O3... no: 4B + 3O2 -> 2B2O3
        "oxide_per_O2": 2/3,
        "phase_patterns": ["B2O3", "BORON_OXIDE", "BORON_TRIOXIDE"],
    },
    "CeO2": {
        "elements": ["CE", "O"],
        "X_O": 2/3,            # CeO2: 1Ce + 2O / 3 atoms = 66.7% O
        "atoms_per_formula": 3,
        "metal_per_O2": 1,     # Ce + O2 -> CeO2
        "oxide_per_O2": 1,
        "phase_patterns": ["FLUORITE", "CEO2", "CERIANITE", "CE_DIOXIDE"],
    },
}


def extract_with_ssub3(session, oxide_name, config, temps):
    """Try to extract Gibbs energy from SSUB3 for a pure oxide."""
    elements = config["elements"]
    X_O = config["X_O"]
    atoms = config["atoms_per_formula"]

    print(f"\n{'='*60}")
    print(f"Extracting {oxide_name} from SSUB3 ({elements})")
    print(f"  X_O = {X_O:.4f}, atoms_per_formula = {atoms}")
    print(f"{'='*60}")

    results = []

    try:
        # Set up system in SSUB3
        system = session.select_database_and_elements("SSUB3", elements).get_system()

        for T in temps:
            try:
                calc = system.with_single_equilibrium_calculation()
                calc.set_condition("T", T)
                calc.set_condition("P", 101325)
                calc.set_condition(f"X(O)", X_O)

                result = calc.calculate()

                # Get system Gibbs energy (per mole of atoms)
                GM = result.get_value_of("GM")

                # Convert: GM (J/mol atoms) -> per formula -> per mol O2
                G_per_formula = GM * atoms
                G_per_O2 = G_per_formula / config["oxide_per_O2"]

                # Subtract reference elements (O2 gas and metal)
                # For Ellingham: dG_f = G(oxide) - G(elements)
                # SSUB3 should already give formation energies relative to SER
                # GM in TC is already referenced to SER (Stable Element Reference)
                # So G_per_O2 IS the formation energy per mol O2

                results.append(G_per_O2)

                if T % 500 == 0:
                    print(f"  T={T}K: GM={GM:.1f} J/mol-at, dG_f={G_per_O2/1000:.1f} kJ/mol O2")

            except Exception as e:
                print(f"  T={T}K: ERROR — {e}")
                results.append(None)

        success = sum(1 for r in results if r is not None)
        print(f"\n  Completed: {success}/{len(temps)} temperatures")
        return results

    except Exception as e:
        print(f"  SSUB3 FAILED for {oxide_name}: {e}")

        # Try alternative: use system GM approach
        print(f"  Trying alternative databases...")
        for alt_db in ["SLAG4", "TCFE14", "TCSLD5", "TCSLD4"]:
            try:
                print(f"  Trying {alt_db}...")
                system = session.select_database_and_elements(alt_db, elements).get_system()

                alt_results = []
                for T in temps:
                    try:
                        calc = system.with_single_equilibrium_calculation()
                        calc.set_condition("T", T)
                        calc.set_condition("P", 101325)
                        calc.set_condition(f"X(O)", X_O)
                        result = calc.calculate()
                        GM = result.get_value_of("GM")
                        G_per_formula = GM * atoms
                        G_per_O2 = G_per_formula / config["oxide_per_O2"]
                        alt_results.append(G_per_O2)
                    except:
                        alt_results.append(None)

                success = sum(1 for r in alt_results if r is not None)
                if success > 0:
                    print(f"  {alt_db}: got {success}/{len(temps)} temperatures")
                    return alt_results
            except Exception as e2:
                print(f"  {alt_db}: {e2}")
                continue

        return [None] * len(temps)


def main():
    print("=" * 60)
    print("SSUB3 Fallback Extraction for Missing Oxides")
    print("PbO, B2O3, CeO2 — not available in TCOX14")
    print("=" * 60)

    if not CSV_PATH.exists():
        print(f"ERROR: Main CSV not found at {CSV_PATH}")
        print("Run extract_oxide_gibbs.py first!")
        return

    # Read existing CSV
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)
        fieldnames = reader.fieldnames

    print(f"\nExisting CSV: {len(existing_rows)} rows, {len(fieldnames)} columns")
    print(f"Temperature range: {existing_rows[0]['T_K']} - {existing_rows[-1]['T_K']} K")

    # Extract from SSUB3
    with TCPython() as session:
        all_results = {}
        for oxide_name, config in FALLBACK_OXIDES.items():
            col_name = f"dG_{oxide_name}_per_O2"
            phase_col = f"oxide_phase_{oxide_name}"

            results = extract_with_ssub3(session, oxide_name, config, TEMPS)
            all_results[oxide_name] = {
                "col": col_name,
                "phase_col": phase_col,
                "values": results,
            }

    # Update CSV
    print(f"\n{'='*60}")
    print("Updating CSV...")

    for oxide_name, data in all_results.items():
        col = data["col"]
        phase_col = data["phase_col"]
        values = data["values"]

        # Add columns if not present
        if col not in fieldnames:
            fieldnames.append(col)
        if phase_col not in fieldnames:
            fieldnames.append(phase_col)

        success_count = 0
        for i, row in enumerate(existing_rows):
            if i < len(values) and values[i] is not None:
                row[col] = f"{values[i]:.4f}"
                row[phase_col] = "SSUB3"
                success_count += 1
            else:
                row[col] = ""
                row[phase_col] = ""

        print(f"  {oxide_name}: wrote {success_count}/{len(existing_rows)} values to {col}")

    # Write updated CSV
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"\nCSV updated: {CSV_PATH}")
    print(f"Total columns: {len(fieldnames)}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("=" * 60)
    for oxide_name, data in all_results.items():
        values = data["values"]
        success = sum(1 for v in values if v is not None)
        if success > 0:
            # Show value at 1000K
            idx_1000 = TEMPS.index(1000)
            val_1000 = values[idx_1000]
            if val_1000 is not None:
                print(f"  {oxide_name}: {success}/{len(TEMPS)} temps, dG_f(1000K) = {val_1000/1000:.1f} kJ/mol O2")
            else:
                print(f"  {oxide_name}: {success}/{len(TEMPS)} temps (no 1000K value)")
        else:
            print(f"  {oxide_name}: FAILED — no data extracted")

    print(f"\nDone. Run verify_oxide_data.py to check results.")


if __name__ == "__main__":
    main()
