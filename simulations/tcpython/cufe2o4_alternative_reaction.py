#!/usr/bin/env python3
"""
Isolate Cu-capture energy from Fe-oxidation energy for CuFe2O4.

The original ternary reaction uses FeO (Fe at +2):
    Cu + 2FeO + O2 -> CuFe2O4       (dG ~ -112 kJ at 1800K)

This includes BOTH Cu capture AND Fe2+ -> Fe3+ oxidation energy.
To isolate the Cu-capture contribution, use Fe2O3 (Fe already at +3):
    Cu + Fe2O3 + 0.5 O2 -> CuFe2O4

The difference between original and alternative dG = Fe oxidation energy.
If the alternative dG is still strongly negative, Cu capture alone drives
the reaction (the desired mechanism). If it's near zero, most of the
-112 kJ came from Fe oxidation (less useful).

Expected: alternative dG less negative than -112 kJ, closer to CuAl2O4's -32 kJ.

Output: ../../data/tcpython/raw/cufe2o4_alternative_reaction.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cufe2o4_alternative_reaction.py
"""

import csv
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 800
T_MAX = 1900
T_STEP = 50  # 23 temperature points

DATABASE = "TCOX14"

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "cufe2o4_alternative_reaction.csv"

# Product: CuFe2O4 (spinel)
# Cu=1, Fe=2, O=4 -> 7 atoms total
PRODUCT_X_CU = 1/7
PRODUCT_X_O = 4/7
PRODUCT_ATOMS = 7

# Alternative reactant: Fe2O3 (hematite)
# Fe=2, O=3 -> 5 atoms total
FE2O3_X_FE = 2/5  # = 0.4
FE2O3_X_O = 3/5   # = 0.6
FE2O3_ATOMS = 5

# Original reactant: FeO (wustite)
# Fe=1, O=1 -> 2 atoms total
FEO_X_O = 1/2
FEO_ATOMS = 2

# Reaction stoichiometry:
#   Alternative: Cu + Fe2O3 + 0.5 O2 -> CuFe2O4
#     n_Cu=1, n_Fe2O3=1 (5 atoms), n_O2=0.5
#   Original:   Cu + 2FeO + O2 -> CuFe2O4
#     n_Cu=1, n_FeO=2 (2 atoms each), n_O2=1.0


def find_phase_gm(result, phase_hints):
    """Search for a specific phase and return its GM value."""
    stable = result.get_stable_phases()
    for hint in phase_hints:
        for phase in stable:
            if hint.upper() in phase.upper():
                try:
                    gm = result.get_value_of("GM({})".format(phase))
                    return gm, phase
                except Exception:
                    pass
    return None, None


def main():
    print("=" * 70)
    print("TC-Python: CuFe2O4 Alternative Reaction (Fe2O3 vs FeO)")
    print("=" * 70)
    print("Database: {}".format(DATABASE))
    print("Temperature range: {}-{} K, step {} K".format(T_MIN, T_MAX, T_STEP))
    print("Output: {}".format(OUTPUT_FILE))
    print("Started: {}".format(datetime.now().isoformat()))
    print()
    print("Alternative: Cu + Fe2O3 + 0.5 O2 -> CuFe2O4  (Fe already +3)")
    print("Original:    Cu + 2FeO  + O2     -> CuFe2O4  (Fe at +2)")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))

    all_rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        # =================================================================
        # Step 1: Cu metal reference (Cu-O system, X_O ~ 0)
        # =================================================================
        print("--- Getting Cu metal reference ---")
        G_Cu_metal = {}
        try:
            cu_system = (session
                         .select_database_and_elements(DATABASE, ["CU", "O"])
                         .get_system())
            for T in temperatures:
                calc = cu_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                    0.0001
                )
                result = calc.calculate()
                G_Cu_metal[T] = result.get_value_of("GM")
            print("  Cu(metal) at 1500K: {:.1f} J/mol-atoms\n".format(
                G_Cu_metal.get(1500, 0)))
        except Exception as e:
            print("  ERROR getting Cu reference: {}\n".format(e))
            return

        # =================================================================
        # Step 2: O2 gas reference (per mol O2)
        # =================================================================
        print("--- Getting O2 gas reference ---")
        G_O2 = {}
        try:
            o2_system = (session
                         .select_database_and_elements(DATABASE, ["O"])
                         .get_system())
            for T in temperatures:
                calc = o2_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                result = calc.calculate()
                G_O2[T] = 2 * result.get_value_of("GM")  # per mol O2
            print("  O2(gas) at 1500K: {:.1f} J/mol-O2\n".format(
                G_O2.get(1500, 0)))
        except Exception as e:
            print("  ERROR getting O2 reference: {}\n".format(e))
            return

        # =================================================================
        # Step 3: Set up Cu-Fe-O ternary system
        # =================================================================
        print("--- Setting up Cu-Fe-O ternary system ---")
        try:
            ternary_system = (session
                              .select_database_and_elements(DATABASE, ["CU", "FE", "O"])
                              .get_system())
        except Exception as e:
            print("  SYSTEM SETUP ERROR: {}".format(e))
            return

        # =================================================================
        # Step 4: Fe2O3 reference (alternative reactant)
        # =================================================================
        print("--- Getting Fe2O3 reference (X_Fe=0.4, X_O=0.6) ---")
        G_Fe2O3 = {}
        for T in temperatures:
            try:
                calc = ternary_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                    0.0001
                )
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                    FE2O3_X_O
                )
                result = calc.calculate()
                G_Fe2O3[T] = result.get_value_of("GM")
            except Exception as e:
                G_Fe2O3[T] = None
                print("  Fe2O3 error at {}K: {}".format(T, e))

        if G_Fe2O3.get(1500):
            print("  Fe2O3 GM at 1500K: {:.1f} J/mol-atoms".format(G_Fe2O3[1500]))

        # =================================================================
        # Step 5: FeO reference (original reactant)
        # =================================================================
        print("--- Getting FeO reference (X_O=0.5) ---")
        G_FeO = {}
        for T in temperatures:
            try:
                calc = ternary_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                    0.0001
                )
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                    FEO_X_O
                )
                result = calc.calculate()
                G_FeO[T] = result.get_value_of("GM")
            except Exception as e:
                G_FeO[T] = None
                print("  FeO error at {}K: {}".format(T, e))

        if G_FeO.get(1500):
            print("  FeO GM at 1500K: {:.1f} J/mol-atoms".format(G_FeO[1500]))

        # =================================================================
        # Step 6: Product-side equilibrium at CuFe2O4 stoichiometry
        # =================================================================
        print("\n--- Calculating CuFe2O4 product at each temperature ---")
        success = 0
        for T in temperatures:
            row = {
                "T_K": T,
                "T_C": T - 273.15,
            }

            try:
                calc = ternary_system.with_single_equilibrium_calculation()
                calc.set_condition(ThermodynamicQuantity.temperature(), T)
                calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                    PRODUCT_X_CU
                )
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                    PRODUCT_X_O
                )
                result = calc.calculate()

                stable = result.get_stable_phases()
                GM_system = result.get_value_of("GM")
                gm_spinel, spinel_phase = find_phase_gm(result, ["SPINEL"])

                row["GM_system_product"] = GM_system
                row["stable_phases"] = "; ".join(stable)
                row["spinel_phase_found"] = spinel_phase if spinel_phase else ""
                row["GM_spinel"] = gm_spinel if gm_spinel else ""
                row["G_Cu_metal"] = G_Cu_metal[T]
                row["G_O2"] = G_O2[T]

                # G_products = GM_system * atoms_per_formula
                G_products = GM_system * PRODUCT_ATOMS

                # --- Alternative reaction: Cu + Fe2O3 + 0.5 O2 -> CuFe2O4 ---
                G_Fe2O3_ref = G_Fe2O3.get(T)
                if G_Fe2O3_ref is not None:
                    G_reactants_alt = (1 * G_Cu_metal[T]
                                       + 1 * FE2O3_ATOMS * G_Fe2O3_ref
                                       + 0.5 * G_O2[T])
                    dG_alt_J = G_products - G_reactants_alt
                    dG_alt_kJ = dG_alt_J / 1000
                    row["dG_alternative_J"] = dG_alt_J
                    row["dG_alternative_kJ"] = dG_alt_kJ
                else:
                    row["dG_alternative_J"] = ""
                    row["dG_alternative_kJ"] = ""

                # --- Original reaction: Cu + 2FeO + O2 -> CuFe2O4 ---
                G_FeO_ref = G_FeO.get(T)
                if G_FeO_ref is not None:
                    G_reactants_orig = (1 * G_Cu_metal[T]
                                        + 2 * FEO_ATOMS * G_FeO_ref
                                        + 1.0 * G_O2[T])
                    dG_orig_J = G_products - G_reactants_orig
                    dG_orig_kJ = dG_orig_J / 1000
                    row["dG_original_J"] = dG_orig_J
                    row["dG_original_kJ"] = dG_orig_kJ
                else:
                    row["dG_original_J"] = ""
                    row["dG_original_kJ"] = ""

                # --- Difference = Fe oxidation contribution ---
                if (row.get("dG_alternative_kJ", "") != ""
                        and row.get("dG_original_kJ", "") != ""):
                    row["dG_Fe_oxidation_kJ"] = dG_orig_kJ - dG_alt_kJ
                else:
                    row["dG_Fe_oxidation_kJ"] = ""

                row["notes"] = ""
                success += 1

            except Exception as e:
                row["GM_system_product"] = ""
                row["stable_phases"] = "ERROR: {}".format(e)
                row["spinel_phase_found"] = ""
                row["GM_spinel"] = ""
                row["G_Cu_metal"] = G_Cu_metal.get(T, "")
                row["G_O2"] = G_O2.get(T, "")
                row["dG_alternative_J"] = ""
                row["dG_alternative_kJ"] = ""
                row["dG_original_J"] = ""
                row["dG_original_kJ"] = ""
                row["dG_Fe_oxidation_kJ"] = ""
                row["notes"] = str(e)

            all_rows.append(row)

        print("  Completed: {}/{} temperatures".format(success, len(temperatures)))

        # Print sample at 1800K
        sample = [r for r in all_rows if r["T_K"] == 1800
                  and r.get("dG_alternative_kJ", "") != ""]
        if sample:
            s = sample[0]
            print("\n  At 1800K:")
            print("    Alternative (Fe2O3): dG = {:+.1f} kJ".format(
                s["dG_alternative_kJ"]))
            print("    Original (FeO):      dG = {:+.1f} kJ".format(
                s["dG_original_kJ"]))
            print("    Fe oxidation contrib: {:.1f} kJ".format(
                s["dG_Fe_oxidation_kJ"]))
            print("    Phases: {}".format(s["stable_phases"]))

    # =====================================================================
    # Write CSV
    # =====================================================================
    fieldnames = [
        "T_K", "T_C", "GM_system_product", "stable_phases",
        "spinel_phase_found", "GM_spinel", "G_Cu_metal", "G_O2",
        "dG_alternative_J", "dG_alternative_kJ",
        "dG_original_J", "dG_original_kJ",
        "dG_Fe_oxidation_kJ", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\n" + "=" * 70)
    print("CSV written to: {}".format(OUTPUT_FILE))
    print("{} rows".format(len(all_rows)))
    print("Finished: {}".format(datetime.now().isoformat()))
    print("=" * 70)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY: CuFe2O4 Reaction Decomposition")
    print("=" * 70)
    print("{:<8} {:>14} {:>14} {:>14}".format(
        "T (K)", "Alt dG (kJ)", "Orig dG (kJ)", "Fe-ox (kJ)"))
    print("-" * 54)
    for r in all_rows:
        if r.get("dG_alternative_kJ", "") != "":
            print("{:<8} {:>+14.1f} {:>+14.1f} {:>14.1f}".format(
                r["T_K"], r["dG_alternative_kJ"],
                r["dG_original_kJ"], r["dG_Fe_oxidation_kJ"]))
    print("=" * 70)


if __name__ == "__main__":
    main()
