#!/usr/bin/env python3
"""
Extract Gibbs energy of FORMATION for oxides from Thermo-Calc TCOX14.

Method:
1. For each oxide, get G of the oxide phase
2. Get G of the metal reference state
3. Get G of O2 gas reference
4. Calculate: dG_f = G(oxide) - n*G(metal) - m*G(O2)
5. Normalize per mole O2 for Ellingham diagram

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

# =============================================================================
# Oxide definitions
# For dG_f calculation: oxide from metal + O2
# Reaction per mole O2: (metal_coeff)*M + O2 -> (oxide_coeff)*MxOy
# =============================================================================
OXIDES = {
    # name: elements, X_O for oxide, metal_coeff per O2, oxide_coeff per O2, phase_patterns
    # phase_patterns: TC phase names to search for (in priority order)
    "Cu2O": {
        "elements": ["CU", "O"],
        "X_O": 0.333,  # Cu2O = 2Cu + 1O, X_O = 1/3
        "metal_per_O2": 4,     # 4Cu + O2 -> 2Cu2O
        "oxide_per_O2": 2,
        "phase_patterns": ["CUPRITE", "CU2O"],
    },
    "CuO": {
        "elements": ["CU", "O"],
        "X_O": 0.500,  # CuO = 1Cu + 1O, X_O = 1/2
        "metal_per_O2": 2,     # 2Cu + O2 -> 2CuO
        "oxide_per_O2": 2,
        "phase_patterns": ["CUO", "TENORITE"],
    },
    "Al2O3": {
        "elements": ["AL", "O"],
        "X_O": 0.600,  # Al2O3 = 2Al + 3O, X_O = 3/5
        "metal_per_O2": 4/3,   # 4/3Al + O2 -> 2/3Al2O3
        "oxide_per_O2": 2/3,
        "phase_patterns": ["CORUNDUM", "AL2O3"],
    },
    "MgO": {
        "elements": ["MG", "O"],
        "X_O": 0.500,  # MgO = 1Mg + 1O
        "metal_per_O2": 2,     # 2Mg + O2 -> 2MgO
        "oxide_per_O2": 2,
        "phase_patterns": ["HALITE", "MGO", "PERICLASE"],
    },
    "SiO2": {
        "elements": ["SI", "O"],
        "X_O": 0.667,  # SiO2 = 1Si + 2O
        "metal_per_O2": 1,     # Si + O2 -> SiO2
        "oxide_per_O2": 1,
        "phase_patterns": ["QUARTZ", "SIO2", "TRIDYMITE", "CRISTOBALITE"],
    },
    "TiO2": {
        "elements": ["TI", "O"],
        "X_O": 0.667,  # TiO2 = 1Ti + 2O
        "metal_per_O2": 1,     # Ti + O2 -> TiO2
        "oxide_per_O2": 1,
        "phase_patterns": ["RUTILE", "TIO2", "ANATASE"],
    },
    "FeO": {
        "elements": ["FE", "O"],
        "X_O": 0.500,  # FeO = 1Fe + 1O
        "metal_per_O2": 2,     # 2Fe + O2 -> 2FeO
        "oxide_per_O2": 2,
        "phase_patterns": ["HALITE", "FEO", "WUSTITE"],  # FeO is halite structure
    },
}


def get_phase_gibbs(result, phase_patterns):
    """
    Get Gibbs energy of a specific phase matching one of the patterns.
    Returns (GM_value, phase_name) or (None, None) if not found.
    """
    stable_phases = result.get_stable_phases()
    for pattern in phase_patterns:
        for phase in stable_phases:
            if pattern.upper() in phase.upper():
                try:
                    gm = result.get_value_of(f"GM({phase})")
                    return gm, phase
                except:
                    pass
    return None, None


def main():
    print("=" * 70)
    print("TC-Python: Oxide Formation Energies for Ellingham Diagram")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))
    print(f"Temperature range: {T_MIN}-{T_MAX} K ({len(temperatures)} points)\n")

    results = {T: {"T_K": T, "T_C": T - 273.15} for T in temperatures}

    with TCPython() as session:
        print("Connected to Thermo-Calc")

        # First, get O2 gas reference energy at each temperature
        print("\n--- Getting O2 reference energies ---")
        G_O2 = {}
        try:
            o2_system = session.select_database_and_elements("TCOX14", ["O"]).get_system()
            for T in temperatures:
                calc = o2_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                result = calc.calculate()
                # O2 gas should be stable phase
                G_O2[T] = result.get_value_of("GM")  # per mole O
            print(f"  O2 reference at 1000K: {G_O2.get(1000, 'N/A')} J/mol-O")
        except Exception as e:
            print(f"  ERROR getting O2: {e}")
            print("  Using G_O2 = 0 (SER reference)")
            G_O2 = {T: 0 for T in temperatures}

        # Process each oxide
        for oxide_name, config in OXIDES.items():
            print(f"\n--- Processing {oxide_name} ---")
            elements = config["elements"]
            X_O = config["X_O"]
            metal = elements[0]

            try:
                system = session.select_database_and_elements("TCOX14", elements).get_system()

                # Get metal reference energy
                print(f"  Getting {metal} reference...")
                G_metal = {}
                for T in temperatures:
                    calc = system.with_single_equilibrium_calculation()
                    calc.set_condition(ThermodynamicQuantity.temperature(), T)
                    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                    calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("O"), 0.0001)  # Nearly pure metal
                    result = calc.calculate()
                    G_metal[T] = result.get_value_of("GM")

                # Get oxide energy at stoichiometric composition
                print(f"  Getting {oxide_name} oxide phase...")
                phase_patterns = config["phase_patterns"]
                success = 0
                for T in temperatures:
                    try:
                        calc = system.with_single_equilibrium_calculation()
                        calc.set_condition(ThermodynamicQuantity.temperature(), T)
                        calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                        calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("O"), X_O)
                        result = calc.calculate()

                        stable = result.get_stable_phases()
                        GM_system = result.get_value_of("GM")

                        # Get the INDIVIDUAL oxide phase Gibbs energy, not mixture
                        GM_oxide, oxide_phase = get_phase_gibbs(result, phase_patterns)

                        # Store raw data
                        results[T][f"GM_{oxide_name}"] = GM_oxide if GM_oxide else GM_system
                        results[T][f"GM_system_{oxide_name}"] = GM_system
                        results[T][f"G_metal_{oxide_name}"] = G_metal[T]
                        results[T][f"phases_{oxide_name}"] = ";".join(stable)
                        results[T][f"oxide_phase_{oxide_name}"] = oxide_phase if oxide_phase else "NOT_FOUND"

                        # Calculate dG_f per mole O2
                        metal_coeff = config["metal_per_O2"]
                        oxide_coeff = config["oxide_per_O2"]

                        # Use individual phase energy if available, else fall back to system
                        GM_for_calc = GM_oxide if GM_oxide else GM_system

                        # dG per mole O2 = oxide_coeff*GM_oxide - metal_coeff*GM_metal - GM_O2
                        dG_per_O2 = oxide_coeff * GM_for_calc - metal_coeff * G_metal[T] - G_O2[T]
                        results[T][f"dG_{oxide_name}_per_O2"] = dG_per_O2

                        success += 1
                    except Exception as e:
                        results[T][f"GM_{oxide_name}"] = None
                        results[T][f"dG_{oxide_name}_per_O2"] = None
                        results[T][f"phases_{oxide_name}"] = f"Error: {e}"

                print(f"  Completed: {success}/{len(temperatures)} temperatures")

                # Sample output
                if 1000 in results and results[1000].get(f"dG_{oxide_name}_per_O2"):
                    dG = results[1000][f"dG_{oxide_name}_per_O2"]
                    phases = results[1000].get(f"phases_{oxide_name}", "")
                    used_phase = results[1000].get(f"oxide_phase_{oxide_name}", "")
                    print(f"  dG at 1000K: {dG/1000:.1f} kJ/mol O2")
                    print(f"  Stable phases: {phases}")
                    print(f"  Used for calc: {used_phase}")

            except Exception as e:
                print(f"  SYSTEM ERROR: {e}")

        # Write CSV
        print(f"\n{'='*70}")
        print(f"Writing to {OUTPUT_FILE}")

        fieldnames = ["T_K", "T_C"]
        for oxide in OXIDES.keys():
            fieldnames.extend([f"GM_{oxide}", f"GM_system_{oxide}", f"G_metal_{oxide}",
                             f"dG_{oxide}_per_O2", f"phases_{oxide}", f"oxide_phase_{oxide}"])

        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for T in temperatures:
                row = {k: results[T].get(k, "") for k in fieldnames}
                writer.writerow(row)

        print(f"Done! {len(temperatures)} rows written.")
        print("=" * 70)


if __name__ == "__main__":
    main()
