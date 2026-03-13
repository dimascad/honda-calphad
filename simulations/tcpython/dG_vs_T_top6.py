#!/usr/bin/env python3
"""
Smooth dG vs T curves for the top 6 ternary reaction products.

Products: CuFe2O4, Cu3V2O8, CuMn2O4, Cu2SiO4, CuB2O4, CuAl2O4
Finer temperature steps: 800-1900K in 25K steps (45 points).

Uses the same dG method as extract_ternary_reactions.py but with:
  - Finer T resolution (25K vs 50K)
  - Only the top 6 products (not all 18)
  - Records stable phases at each T to identify phase transition kinks

This data is used for publication-quality dG vs T figures.

Output: ../../data/tcpython/raw/dG_vs_T_top6.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" dG_vs_T_top6.py
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
T_STEP = 25  # finer resolution: 45 points

DATABASE = "TCOX14"

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "dG_vs_T_top6.csv"

# =============================================================================
# Top 6 products with full stoichiometry definitions
# (Same structure as extract_ternary_reactions.py TERNARY_SYSTEMS)
# =============================================================================
TOP6 = [
    {
        "product": "CuFe2O4",
        "name": "copper ferrite spinel",
        "oxide": "FeO",
        "metal": "FE",
        "reaction": "Cu + 2FeO + O2 -> CuFe2O4",
        "X_Cu": 1/7, "X_O": 4/7,
        "atoms_per_formula": 7,
        "phase_hints": ["SPINEL"],
        "n_Cu": 1, "n_oxide_fu": 2, "oxide_atoms": 2, "n_O2": 1.0,
        "oxide_X_O": 1/2,  # FeO
    },
    {
        "product": "Cu3V2O8",
        "name": "copper orthovanadate",
        "oxide": "V2O5",
        "metal": "V",
        "reaction": "3Cu + V2O5 + 1.5 O2 -> Cu3V2O8",
        "X_Cu": 3/13, "X_O": 8/13,
        "atoms_per_formula": 13,
        "phase_hints": ["ORTHOVANADATE", "CU3V2O8"],
        "n_Cu": 3, "n_oxide_fu": 1, "oxide_atoms": 7, "n_O2": 1.5,
        "oxide_X_O": 5/7,  # V2O5
    },
    {
        "product": "CuMn2O4",
        "name": "copper manganite spinel",
        "oxide": "MnO",
        "metal": "MN",
        "reaction": "Cu + 2MnO + O2 -> CuMn2O4",
        "X_Cu": 1/7, "X_O": 4/7,
        "atoms_per_formula": 7,
        "phase_hints": ["SPINEL"],
        "n_Cu": 1, "n_oxide_fu": 2, "oxide_atoms": 2, "n_O2": 1.0,
        "oxide_X_O": 1/2,  # MnO
    },
    {
        "product": "Cu2SiO4",
        "name": "copper orthosilicate",
        "oxide": "SiO2",
        "metal": "SI",
        "reaction": "2Cu + SiO2 + O2 -> Cu2SiO4",
        "X_Cu": 2/7, "X_O": 4/7,
        "atoms_per_formula": 7,
        "phase_hints": ["OLIVINE", "CU2SIO4"],
        "n_Cu": 2, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 1.0,
        "oxide_X_O": 2/3,  # SiO2
    },
    {
        "product": "CuB2O4",
        "name": "copper borate",
        "oxide": "B2O3",
        "metal": "B",
        "reaction": "Cu + B2O3 + 0.5 O2 -> CuB2O4",
        "X_Cu": 1/7, "X_O": 4/7,
        "atoms_per_formula": 7,
        "phase_hints": ["BORATE", "CUBO", "CUB2O4"],
        "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 5, "n_O2": 0.5,
        "oxide_X_O": 3/5,  # B2O3
    },
    {
        "product": "CuAl2O4",
        "name": "copper aluminate spinel",
        "oxide": "Al2O3",
        "metal": "AL",
        "reaction": "Cu + Al2O3 + 0.5 O2 -> CuAl2O4",
        "X_Cu": 1/7, "X_O": 4/7,
        "atoms_per_formula": 7,
        "phase_hints": ["SPINEL"],
        "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 5, "n_O2": 0.5,
        "oxide_X_O": 3/5,  # Al2O3
    },
]


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
    print("TC-Python: dG vs T for Top 6 Ternary Products (fine resolution)")
    print("=" * 70)
    print("Database: {}".format(DATABASE))
    print("Temperature range: {}-{} K, step {} K ({} points)".format(
        T_MIN, T_MAX, T_STEP, len(range(T_MIN, T_MAX + 1, T_STEP))))
    print("Products: {}".format(", ".join(p["product"] for p in TOP6)))
    print("Output: {}".format(OUTPUT_FILE))
    print("Started: {}".format(datetime.now().isoformat()))
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))

    all_rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        # =================================================================
        # Step 1: Cu metal reference
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
        # Step 2: O2 gas reference
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
        # Step 3: For each product, set up system and calculate
        # =================================================================
        for prod_def in TOP6:
            product = prod_def["product"]
            metal = prod_def["metal"]
            oxide = prod_def["oxide"]

            print("\n" + "=" * 60)
            print("Product: {} ({})".format(product, prod_def["name"]))
            print("System: Cu-{}-O  (reactant oxide = {})".format(metal, oxide))
            print("Reaction: {}".format(prod_def["reaction"]))
            print("=" * 60)

            # Set up ternary system
            try:
                ternary_system = (session
                                  .select_database_and_elements(
                                      DATABASE, ["CU", metal, "O"])
                                  .get_system())
            except Exception as e:
                print("  SYSTEM SETUP ERROR: {}".format(e))
                for T in temperatures:
                    all_rows.append({
                        "T_K": T, "T_C": T - 273.15,
                        "product": product, "product_name": prod_def["name"],
                        "oxide": oxide, "reaction": prod_def["reaction"],
                        "GM_system_product": "",
                        "stable_phases": "ERROR: {}".format(e),
                        "ternary_phase_found": "", "GM_ternary_phase": "",
                        "G_Cu_metal": "", "G_O2": "",
                        "dG_rxn_system_J": "", "dG_rxn_system_kJ": "",
                        "notes": "System setup failed",
                    })
                continue

            # Binary oxide reference
            print("  Getting {} reference...".format(oxide))
            G_binary_oxide = {}
            oxide_X_O = prod_def["oxide_X_O"]

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
                        oxide_X_O
                    )
                    result = calc.calculate()
                    G_binary_oxide[T] = result.get_value_of("GM")
                except Exception:
                    G_binary_oxide[T] = None

            # Product equilibrium at each T
            success = 0
            for T in temperatures:
                row = {
                    "T_K": T,
                    "T_C": T - 273.15,
                    "product": product,
                    "product_name": prod_def["name"],
                    "oxide": oxide,
                    "reaction": prod_def["reaction"],
                }

                try:
                    calc = ternary_system.with_single_equilibrium_calculation()
                    calc.set_condition(ThermodynamicQuantity.temperature(), T)
                    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                        prod_def["X_Cu"]
                    )
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                        prod_def["X_O"]
                    )
                    result = calc.calculate()

                    stable = result.get_stable_phases()
                    GM_system = result.get_value_of("GM")
                    gm_ternary, ternary_phase = find_phase_gm(
                        result, prod_def["phase_hints"])

                    row["GM_system_product"] = GM_system
                    row["stable_phases"] = "; ".join(stable)
                    row["ternary_phase_found"] = ternary_phase if ternary_phase else ""
                    row["GM_ternary_phase"] = gm_ternary if gm_ternary else ""
                    row["G_Cu_metal"] = G_Cu_metal[T]
                    row["G_O2"] = G_O2[T]

                    # dG calculation
                    G_oxide_ref = G_binary_oxide.get(T)
                    if G_oxide_ref is not None:
                        atoms = prod_def["atoms_per_formula"]
                        G_products = GM_system * atoms

                        G_reactants = (prod_def["n_Cu"] * G_Cu_metal[T]
                                       + prod_def["n_oxide_fu"]
                                       * prod_def["oxide_atoms"] * G_oxide_ref
                                       + prod_def["n_O2"] * G_O2[T])

                        dG_rxn_J = G_products - G_reactants
                        dG_rxn_kJ = dG_rxn_J / 1000

                        row["dG_rxn_system_J"] = dG_rxn_J
                        row["dG_rxn_system_kJ"] = dG_rxn_kJ
                        row["notes"] = ""
                    else:
                        row["dG_rxn_system_J"] = ""
                        row["dG_rxn_system_kJ"] = ""
                        row["notes"] = "No binary oxide reference"

                    success += 1

                except Exception as e:
                    row["GM_system_product"] = ""
                    row["stable_phases"] = "ERROR: {}".format(e)
                    row["ternary_phase_found"] = ""
                    row["GM_ternary_phase"] = ""
                    row["G_Cu_metal"] = G_Cu_metal.get(T, "")
                    row["G_O2"] = G_O2.get(T, "")
                    row["dG_rxn_system_J"] = ""
                    row["dG_rxn_system_kJ"] = ""
                    row["notes"] = str(e)

                all_rows.append(row)

            print("  Completed: {}/{} temperatures".format(success, len(temperatures)))

            # Sample at 1800K
            sample = [r for r in all_rows if r["T_K"] == 1800
                      and r["product"] == product
                      and r.get("dG_rxn_system_kJ", "") != ""]
            if sample:
                s = sample[0]
                verdict = "FAVORABLE" if s["dG_rxn_system_kJ"] < 0 else "Unfavorable"
                print("  At 1800K: dG = {:+.1f} kJ -> {}".format(
                    s["dG_rxn_system_kJ"], verdict))
                print("  Phases: {}".format(s["stable_phases"]))

    # =========================================================================
    # Write CSV
    # =========================================================================
    fieldnames = [
        "T_K", "T_C", "product", "product_name", "oxide", "reaction",
        "GM_system_product", "stable_phases", "ternary_phase_found",
        "GM_ternary_phase", "G_Cu_metal", "G_O2",
        "dG_rxn_system_J", "dG_rxn_system_kJ", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print("\n" + "=" * 70)
    print("CSV written to: {}".format(OUTPUT_FILE))
    print("{} rows ({} products x {} temperatures)".format(
        len(all_rows), len(TOP6), len(temperatures)))
    print("Finished: {}".format(datetime.now().isoformat()))
    print("=" * 70)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY: dG at Key Temperatures (kJ/mol)")
    print("=" * 70)
    print("{:<14} {:>10} {:>10} {:>10} {:>10}".format(
        "Product", "1000K", "1400K", "1600K", "1800K"))
    print("-" * 58)

    for prod_def in TOP6:
        product = prod_def["product"]
        prod_rows = [r for r in all_rows if r["product"] == product]
        vals = {}
        for r in prod_rows:
            if r.get("dG_rxn_system_kJ", "") != "":
                for target in [1000, 1400, 1600, 1800]:
                    if abs(r["T_K"] - target) < 15:
                        vals[target] = r["dG_rxn_system_kJ"]
        line = "{:<14}".format(product)
        for target in [1000, 1400, 1600, 1800]:
            if target in vals:
                line += " {:>+10.1f}".format(vals[target])
            else:
                line += " {:>10}".format("N/A")
        print(line)

    print("=" * 70)


if __name__ == "__main__":
    main()
