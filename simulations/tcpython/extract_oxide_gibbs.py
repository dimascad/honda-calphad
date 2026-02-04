#!/usr/bin/env python3
"""
Extract Gibbs energy of formation for oxides from Thermo-Calc SSUB database.

This script calculates dGf (per mole O2) for Ellingham diagram comparison:
- Cu2O, CuO (copper oxides)
- Al2O3 (corundum)
- MgO (periclase)
- SiO2 (quartz/cristobalite)
- TiO2 (rutile)
- FeO (wustite)

Output: ../../data/tcpython/raw/oxide_gibbs_energies.csv

Run on OSU lab machine:
    "C:\Program Files\Thermo-Calc\2025b\python\python.exe" extract_oxide_gibbs.py
"""

import os
import csv
from pathlib import Path

# TC-Python import
try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not found. Run this on OSU lab machine.")
    print("Python: C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe")
    exit(1)

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 500       # K
T_MAX = 2000      # K
T_STEP = 50       # K
DATABASE = "SSUB6"  # Pure substances database (try SSUB6, SSUB5, or SSUB3)

# Output path (relative to script location)
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "oxide_gibbs_energies.csv"

# =============================================================================
# Oxide definitions
# Reaction format: coefficient * metal + O2_coeff * O2 -> oxide
# We normalize to per mole O2 for Ellingham diagram
# =============================================================================
OXIDES = {
    # Oxide: (phase_name, metal, metal_phase, metal_coeff, O2_coeff, formula_for_comments)
    "Cu2O":  ("CU2O",    "CU", "FCC_A1",   4,   1, "4Cu + O2 -> 2Cu2O"),
    "CuO":   ("CUO",     "CU", "FCC_A1",   2,   1, "2Cu + O2 -> 2CuO"),
    "Al2O3": ("CORUNDUM","AL", "FCC_A1",   4/3, 1, "4/3Al + O2 -> 2/3Al2O3"),
    "MgO":   ("PERICLASE","MG","HCP_A3",   2,   1, "2Mg + O2 -> 2MgO"),
    "SiO2":  ("QUARTZ",  "SI", "DIAMOND_A4", 1, 1, "Si + O2 -> SiO2"),
    "TiO2":  ("RUTILE",  "TI", "HCP_A3",   1,   1, "Ti + O2 -> TiO2"),
    "FeO":   ("HALITE",  "FE", "BCC_A2",   2,   1, "2Fe + O2 -> 2FeO"),
}

# =============================================================================
# Main calculation
# =============================================================================
def main():
    print("=" * 70)
    print("TC-Python: Extracting Oxide Gibbs Energies for Ellingham Diagram")
    print("=" * 70)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Temperature range
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))
    print(f"Temperature range: {T_MIN}-{T_MAX} K, step {T_STEP} K ({len(temperatures)} points)")

    # Results storage
    results = {T: {"T_K": T, "T_C": T - 273.15} for T in temperatures}

    with TCPython() as session:
        print(f"\nConnected to Thermo-Calc")

        # List available databases
        databases = session.get_databases()
        print(f"Available databases: {databases[:10]}...")  # First 10

        if DATABASE not in databases:
            print(f"WARNING: {DATABASE} not found. Trying alternatives...")
            for alt in ["SSUB6", "SSUB5", "SSUB3", "PURE5"]:
                if alt in databases:
                    print(f"Using {alt} instead")
                    db_name = alt
                    break
            else:
                print("ERROR: No pure substance database found!")
                return
        else:
            db_name = DATABASE

        # Calculate Gibbs energy for O2 gas (reference)
        print(f"\nCalculating O2 reference (from {db_name})...")
        try:
            o2_system = session.select_database_and_elements(db_name, ["O"]).get_system()
            o2_calc = o2_system.with_single_equilibrium_calculation()
            o2_calc.set_condition(ThermodynamicQuantity.pressure(), 101325)

            G_O2 = {}
            for T in temperatures:
                o2_calc.set_condition(ThermodynamicQuantity.temperature(), T)
                o2_result = o2_calc.calculate()
                # Get Gibbs energy of O2 gas phase
                G_O2[T] = o2_result.get_value_of("G(GAS)")
            print(f"  G(O2) at 1000K: {G_O2.get(1000, 'N/A'):.0f} J/mol")
        except Exception as e:
            print(f"  Error calculating O2: {e}")
            print("  Using SGTE reference (G=0 for elements)")
            G_O2 = {T: 0 for T in temperatures}

        # Calculate each oxide
        for oxide_name, (phase, metal, metal_phase, metal_coeff, o2_coeff, reaction) in OXIDES.items():
            print(f"\n{oxide_name}: {reaction}")

            try:
                # Get system with metal and oxygen
                elements = [metal, "O"]
                system = session.select_database_and_elements(db_name, elements).get_system()
                calc = system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)

                for T in temperatures:
                    calc.set_condition(ThermodynamicQuantity.temperature(), T)

                    try:
                        result = calc.calculate()

                        # Try to get Gibbs energy of the oxide phase
                        try:
                            G_oxide = result.get_value_of(f"G({phase})")
                        except:
                            # Try alternative phase names
                            alt_phases = [oxide_name, phase.upper(), phase.lower()]
                            G_oxide = None
                            for alt in alt_phases:
                                try:
                                    G_oxide = result.get_value_of(f"G({alt})")
                                    break
                                except:
                                    continue
                            if G_oxide is None:
                                G_oxide = float('nan')

                        # Get metal reference
                        try:
                            G_metal = result.get_value_of(f"G({metal_phase})")
                        except:
                            G_metal = 0  # SGTE reference

                        # Calculate formation energy per mole O2
                        # dGf = G(oxide) - metal_coeff*G(metal) - o2_coeff*G(O2)
                        # Normalized per mole O2
                        if not (G_oxide != G_oxide):  # Check for NaN
                            dG_formation = G_oxide - metal_coeff * G_metal - o2_coeff * G_O2[T]
                            results[T][f"dG_{oxide_name}_per_O2"] = dG_formation
                        else:
                            results[T][f"dG_{oxide_name}_per_O2"] = float('nan')

                    except Exception as e:
                        results[T][f"dG_{oxide_name}_per_O2"] = float('nan')
                        if T == T_MIN:
                            print(f"  Warning at {T}K: {e}")

                # Report sample value
                sample_T = 1273  # 1000C
                if sample_T in results and f"dG_{oxide_name}_per_O2" in results[sample_T]:
                    val = results[sample_T][f"dG_{oxide_name}_per_O2"]
                    if val == val:  # Not NaN
                        print(f"  dG at 1000C: {val/1000:.1f} kJ/mol O2")
                    else:
                        print(f"  dG at 1000C: calculation failed")

            except Exception as e:
                print(f"  ERROR: {e}")
                for T in temperatures:
                    results[T][f"dG_{oxide_name}_per_O2"] = float('nan')

    # Write CSV
    print(f"\n{'=' * 70}")
    print(f"Writing results to: {OUTPUT_FILE}")

    fieldnames = ["T_K", "T_C"] + [f"dG_{ox}_per_O2" for ox in OXIDES.keys()]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for T in temperatures:
            row = {k: results[T].get(k, '') for k in fieldnames}
            writer.writerow(row)

    print(f"Done! {len(temperatures)} data points written.")
    print(f"\nNext steps:")
    print(f"  1. git add data/tcpython/raw/oxide_gibbs_energies.csv")
    print(f"  2. git commit -m 'TC-Python: oxide Gibbs energies from SSUB'")
    print(f"  3. git push")
    print("=" * 70)


if __name__ == "__main__":
    main()
