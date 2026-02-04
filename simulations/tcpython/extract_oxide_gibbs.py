#!/usr/bin/env python3
"""
Extract Gibbs energy of formation for oxides from Thermo-Calc TCOX14.
Output: ../../data/tcpython/raw/oxide_gibbs_energies.csv
"""

import csv
from pathlib import Path
from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 500
T_MAX = 2000
T_STEP = 50

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "oxide_gibbs_energies.csv"

# Oxide compositions: X(Metal), X(O) for stoichiometric oxide
# These will find equilibrium and get the oxide phase Gibbs energy
OXIDES = {
    "Cu2O": {"elements": ["CU", "O"], "X_O": 0.333},   # Cu2O: 2Cu + 1O
    "CuO":  {"elements": ["CU", "O"], "X_O": 0.500},   # CuO: 1Cu + 1O
    "Al2O3":{"elements": ["AL", "O"], "X_O": 0.600},   # Al2O3: 2Al + 3O
    "MgO":  {"elements": ["MG", "O"], "X_O": 0.500},   # MgO: 1Mg + 1O
    "SiO2": {"elements": ["SI", "O"], "X_O": 0.667},   # SiO2: 1Si + 2O
    "TiO2": {"elements": ["TI", "O"], "X_O": 0.667},   # TiO2: 1Ti + 2O
    "FeO":  {"elements": ["FE", "O"], "X_O": 0.500},   # FeO: 1Fe + 1O
}

def main():
    print("=" * 70)
    print("TC-Python: Extracting Oxide Gibbs Energies (TCOX14)")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))
    print(f"Temperature range: {T_MIN}-{T_MAX} K ({len(temperatures)} points)")

    results = {T: {"T_K": T, "T_C": T - 273.15} for T in temperatures}

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        for oxide_name, config in OXIDES.items():
            elements = config["elements"]
            X_O = config["X_O"]

            print(f"Processing {oxide_name} ({elements})...")

            try:
                system = (session
                    .select_database_and_elements("TCOX14", elements)
                    .get_system())

                for T in temperatures:
                    try:
                        calc = system.with_single_equilibrium_calculation()
                        calc.set_condition(ThermodynamicQuantity.temperature(), T)
                        calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                        calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("O"), X_O)

                        result = calc.calculate()

                        # Get total Gibbs energy and stable phases
                        G = result.get_value_of("G")
                        GM = result.get_value_of("GM")
                        stable = result.get_stable_phases()

                        results[T][f"G_{oxide_name}"] = G
                        results[T][f"GM_{oxide_name}"] = GM
                        results[T][f"phases_{oxide_name}"] = ";".join(stable)

                    except Exception as e:
                        results[T][f"G_{oxide_name}"] = None
                        results[T][f"GM_{oxide_name}"] = None
                        results[T][f"phases_{oxide_name}"] = f"Error: {e}"

                # Sample output
                sample_T = 1273
                if results[sample_T].get(f"GM_{oxide_name}"):
                    print(f"  GM at 1000C: {results[sample_T][f'GM_{oxide_name}']:.0f} J/mol")
                    print(f"  Phases: {results[sample_T][f'phases_{oxide_name}']}")

            except Exception as e:
                print(f"  ERROR: {e}")
                for T in temperatures:
                    results[T][f"G_{oxide_name}"] = None
                    results[T][f"GM_{oxide_name}"] = None
                    results[T][f"phases_{oxide_name}"] = f"Error: {e}"

            print()

    # Write CSV
    print(f"Writing to {OUTPUT_FILE}")

    # Build fieldnames
    fieldnames = ["T_K", "T_C"]
    for oxide in OXIDES.keys():
        fieldnames.extend([f"G_{oxide}", f"GM_{oxide}", f"phases_{oxide}"])

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for T in temperatures:
            row = {k: results[T].get(k, "") for k in fieldnames}
            writer.writerow(row)

    print(f"Done! {len(temperatures)} rows written.")
    print("=" * 70)
    print("Next: Copy the CSV to your Mac and process it.")
    print("=" * 70)


if __name__ == "__main__":
    main()
