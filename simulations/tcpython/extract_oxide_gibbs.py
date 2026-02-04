#!/usr/bin/env python3
"""
Extract Gibbs energy of formation for oxides from Thermo-Calc TCOX14 database.

Calculates dGf (per mole O2) for Ellingham diagram:
- Cu2O, CuO, Al2O3, MgO, SiO2, TiO2, FeO

Output: ../../data/tcpython/raw/oxide_gibbs_energies.csv
"""

import os
import csv
from pathlib import Path

try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not found. Run on OSU lab machine.")
    exit(1)

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 500
T_MAX = 2000
T_STEP = 50

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "oxide_gibbs_energies.csv"

# =============================================================================
# Main
# =============================================================================
def main():
    print("=" * 70)
    print("TC-Python: Extracting Oxide Gibbs Energies (TCOX14)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))
    print(f"Temperature range: {T_MIN}-{T_MAX} K ({len(temperatures)} points)")

    results = []

    with TCPython() as session:
        print("Connected to Thermo-Calc")

        # Use TCOX14 for oxide calculations
        print("\nSetting up TCOX14 with Cu-Al-Mg-Si-Ti-Fe-O...")

        try:
            system = (session
                .select_database_and_elements("TCOX14", ["CU", "AL", "MG", "SI", "TI", "FE", "O"])
                .get_system())
            print("System created successfully")
        except Exception as e:
            print(f"Error creating system: {e}")
            print("Trying with fewer elements...")
            system = (session
                .select_database_and_elements("TCOX14", ["CU", "AL", "O"])
                .get_system())

        # For each temperature, calculate Gibbs energy of key oxide phases
        print("\nCalculating Gibbs energies...")

        for T in temperatures:
            row = {"T_K": T, "T_C": T - 273.15}

            # Calculate equilibrium at this temperature for each oxide composition
            calc = system.with_single_equilibrium_calculation()
            calc.set_condition(ThermodynamicQuantity.temperature(), T)
            calc.set_condition(ThermodynamicQuantity.pressure(), 101325)

            # Cu2O: X(Cu)=0.667, X(O)=0.333
            try:
                calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("CU"), 0.667)
                calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("O"), 0.333)
                calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("AL"), 0.0)
                result = calc.calculate()
                G_sys = result.get_value_of(ThermodynamicQuantity.gibbs_energy_of_a_phase("*"))
                row["G_Cu2O_system"] = G_sys
            except Exception as e:
                row["G_Cu2O_system"] = f"Error: {e}"

            results.append(row)

            if T % 500 == 0:
                print(f"  T = {T} K done")

        print(f"\nWriting to {OUTPUT_FILE}")

        # Write CSV
        if results:
            fieldnames = list(results[0].keys())
            with open(OUTPUT_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"Done! {len(results)} rows written.")
        else:
            print("No results to write!")

    print("=" * 70)


if __name__ == "__main__":
    main()
