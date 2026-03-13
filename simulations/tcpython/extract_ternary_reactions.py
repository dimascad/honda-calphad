#!/usr/bin/env python3
"""
Extract Gibbs energies for TERNARY REACTION products (Cu + oxide → complex).

This script calculates the Gibbs energy of ternary compound formation
for copper interacting with each screening oxide. The key question:
  "Can Cu react with MOx to form a ternary compound (spinel, vanadate, etc.)?"

Method for each oxide (e.g., Al2O3):
  1. Set up Cu-M-O ternary system in TCOX14
  2. At the ternary compound stoichiometry (e.g., CuAl2O4), calculate equilibrium
  3. Extract G of the ternary phase (SPINEL, etc.) if stable
  4. Also extract G of the binary oxide phase and Cu metal for comparison
  5. Calculate: dG_rxn = G(CuMOy) - G(Cu) - G(MOx)
  6. If dG_rxn < 0, the reaction is favorable → oxide can capture copper

Approach:
  For each oxide at each temperature, we run TWO equilibrium calculations:
    A) "Reactant side": separate Cu metal + pure oxide
       (reuse G_metal and G_oxide from extract_oxide_gibbs.py data)
    B) "Product side": Cu-M-O system at ternary compound stoichiometry
       → let TC find the equilibrium phases (may include spinel, delafossite, etc.)
       → use SYSTEM Gibbs energy (GM * total atoms) as G_products

  dG_rxn = G_products_system - G_reactants_sum

  If the system prefers to form a ternary compound, G_products < G_reactants
  and dG_rxn < 0 (favorable).

Output: ../../data/tcpython/raw/ternary_reaction_energies.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" extract_ternary_reactions.py
"""

import csv
import os
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 800
T_MAX = 1900
T_STEP = 50  # finer step in steelmaking range

DATABASE = "TCOX14"

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "ternary_reaction_energies.csv"

# =============================================================================
# Ternary compound definitions
#
# For each oxide, we define:
#   - elements: [METAL, "O"] for the binary oxide (Cu is always added)
#   - ternary_formulas: list of known Cu-M-O compounds to check
#   - For each ternary formula:
#       - name: human-readable name
#       - composition: {element: mole_fraction} for the ternary stoichiometry
#       - atoms_per_formula: total atoms in one formula unit
#       - reaction: string description of the balanced reaction
#       - phase_hints: TC phase names to look for (SPINEL, etc.)
#       - reactant_oxide_atoms: atoms per formula in the reactant oxide
#       - cu_atoms: Cu atoms consumed per formula unit of product
#
# Stoichiometric compositions for ternary compounds:
#   CuAl2O4: Cu=1, Al=2, O=4 → total 7 atoms → X_Cu=1/7, X_Al=2/7, X_O=4/7
#   CuFe2O4: Cu=1, Fe=2, O=4 → total 7 atoms → same fractions
#   CuCr2O4: Cu=1, Cr=2, O=4 → total 7 atoms → same fractions
#   CuMn2O4: Cu=1, Mn=2, O=4 → total 7 atoms → same fractions
#   CuV2O6:  Cu=1, V=2, O=6  → total 9 atoms → X_Cu=1/9, X_V=2/9, X_O=6/9
#   CuTiO3:  Cu=1, Ti=1, O=3 → total 5 atoms → X_Cu=1/5, X_Ti=1/5, X_O=3/5
#   CuSiO3:  Cu=1, Si=1, O=3 → total 5 atoms → same as CuTiO3
#   CuAlO2:  Cu=1, Al=1, O=2 → total 4 atoms → X_Cu=1/4, X_Al=1/4, X_O=2/4
# =============================================================================

TERNARY_SYSTEMS = [
    # --- SPINEL-FORMING OXIDES ---
    # Spinel: CuM2O4 = Cu + M2O3 + 0.5 O2
    #   Reactant stoich per formula: 1 Cu + 1 M2O3 (5 atoms) + 0.5 O2 (1 O atom)
    #   So: n_Cu=1, n_oxide=1, n_O2=0.5, oxide_atoms=5
    {
        "oxide": "Al2O3",
        "metal": "AL",
        "ternaries": [
            {
                "product": "CuAl2O4",
                "name": "copper aluminate spinel",
                "reaction": "Cu + Al2O3 + 0.5 O2 -> CuAl2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["SPINEL"],
                # Reactant-side stoichiometry for dG_rxn
                "n_Cu": 1,          # moles Cu metal consumed
                "n_oxide_fu": 1,    # moles of oxide formula units consumed
                "oxide_atoms": 5,   # atoms per oxide formula unit (Al2O3)
                "n_O2": 0.5,        # moles O2 consumed (can be 0 if no extra O)
            },
            {
                "product": "CuAlO2",
                "name": "delafossite",
                "reaction": "Cu + 0.5 Al2O3 + 0.25 O2 -> CuAlO2",
                "X_Cu": 1/4, "X_M": 1/4, "X_O": 2/4,
                "atoms_per_formula": 4,
                "phase_hints": ["DELAFOSSITE", "CUALUMINATE", "CUALOXID"],
                "n_Cu": 1, "n_oxide_fu": 0.5, "oxide_atoms": 5, "n_O2": 0.25,
            },
        ],
    },
    {
        "oxide": "Cr2O3",
        "metal": "CR",
        "ternaries": [
            {
                "product": "CuCr2O4",
                "name": "copper chromite spinel",
                "reaction": "Cu + Cr2O3 + 0.5 O2 -> CuCr2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["SPINEL"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 5, "n_O2": 0.5,
            },
        ],
    },
    {
        "oxide": "MnO",
        "metal": "MN",
        "ternaries": [
            {
                "product": "CuMn2O4",
                "name": "copper manganite spinel",
                "reaction": "Cu + 2MnO + O2 -> CuMn2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["SPINEL"],
                "n_Cu": 1, "n_oxide_fu": 2, "oxide_atoms": 2, "n_O2": 1.0,
            },
        ],
    },
    {
        "oxide": "FeO",
        "metal": "FE",
        "ternaries": [
            {
                "product": "CuFe2O4",
                "name": "copper ferrite spinel",
                "reaction": "Cu + 2FeO + O2 -> CuFe2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["SPINEL"],
                "n_Cu": 1, "n_oxide_fu": 2, "oxide_atoms": 2, "n_O2": 1.0,
            },
        ],
    },
    # --- VANADATE/COMPLEX OXIDE ---
    {
        "oxide": "V2O5",
        "metal": "V",
        "ternaries": [
            {
                "product": "CuV2O6",
                "name": "copper vanadate",
                "reaction": "Cu + V2O5 + 0.5 O2 -> CuV2O6",
                "X_Cu": 1/9, "X_M": 2/9, "X_O": 6/9,
                "atoms_per_formula": 9,
                "phase_hints": ["VANADATE", "CUV2O6"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 7, "n_O2": 0.5,
            },
            {
                "product": "Cu3V2O8",
                "name": "copper orthovanadate",
                "reaction": "3Cu + V2O5 + 1.5 O2 -> Cu3V2O8",
                "X_Cu": 3/13, "X_M": 2/13, "X_O": 8/13,
                "atoms_per_formula": 13,
                "phase_hints": ["ORTHOVANADATE", "CU3V2O8"],
                "n_Cu": 3, "n_oxide_fu": 1, "oxide_atoms": 7, "n_O2": 1.5,
            },
        ],
    },
    # --- TITANATE ---
    {
        "oxide": "TiO2",
        "metal": "TI",
        "ternaries": [
            {
                "product": "CuTiO3",
                "name": "copper titanate",
                "reaction": "Cu + TiO2 + 0.5 O2 -> CuTiO3",
                "X_Cu": 1/5, "X_M": 1/5, "X_O": 3/5,
                "atoms_per_formula": 5,
                "phase_hints": ["ILMENITE", "CUTIO3", "PEROVSKITE"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 0.5,
            },
        ],
    },
    # --- SILICATE ---
    {
        "oxide": "SiO2",
        "metal": "SI",
        "ternaries": [
            {
                "product": "CuSiO3",
                "name": "copper metasilicate",
                "reaction": "Cu + SiO2 + 0.5 O2 -> CuSiO3",
                "X_Cu": 1/5, "X_M": 1/5, "X_O": 3/5,
                "atoms_per_formula": 5,
                "phase_hints": ["PYROXENE", "CUSIO3", "WOLLASTONITE"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 0.5,
            },
            {
                "product": "Cu2SiO4",
                "name": "copper orthosilicate",
                "reaction": "2Cu + SiO2 + O2 -> Cu2SiO4",
                "X_Cu": 2/7, "X_M": 1/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["OLIVINE", "CU2SIO4"],
                "n_Cu": 2, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 1.0,
            },
        ],
    },
    # --- SIMPLE OXIDES (less likely to form ternaries, but check) ---
    {
        "oxide": "MgO",
        "metal": "MG",
        "ternaries": [
            {
                "product": "CuMgO2",
                "name": "copper magnesioxide (hypothetical)",
                "reaction": "Cu + MgO + 0.5 O2 -> CuMgO2",
                "X_Cu": 1/4, "X_M": 1/4, "X_O": 2/4,
                "atoms_per_formula": 4,
                "phase_hints": ["DELAFOSSITE", "CUMGO2"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 2, "n_O2": 0.5,
            },
        ],
    },
    {
        "oxide": "CaO",
        "metal": "CA",
        "ternaries": [
            {
                "product": "CuCaO2",
                "name": "copper calcioxide (hypothetical)",
                "reaction": "Cu + CaO + 0.5 O2 -> CuCaO2",
                "X_Cu": 1/4, "X_M": 1/4, "X_O": 2/4,
                "atoms_per_formula": 4,
                "phase_hints": ["DELAFOSSITE", "CUCAO2"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 2, "n_O2": 0.5,
            },
        ],
    },
    {
        "oxide": "ZrO2",
        "metal": "ZR",
        "ternaries": [
            {
                "product": "CuZrO3",
                "name": "copper zirconate (hypothetical)",
                "reaction": "Cu + ZrO2 + 0.5 O2 -> CuZrO3",
                "X_Cu": 1/5, "X_M": 1/5, "X_O": 3/5,
                "atoms_per_formula": 5,
                "phase_hints": ["PEROVSKITE", "CUZRO3"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 0.5,
            },
        ],
    },
    # --- MOONSHOT OXIDES ---
    {
        "oxide": "NiO",
        "metal": "NI",
        "ternaries": [
            {
                "product": "CuNiO2",
                "name": "copper nickelate",
                "reaction": "Cu + NiO + 0.5 O2 -> CuNiO2",
                "X_Cu": 1/4, "X_M": 1/4, "X_O": 2/4,
                "atoms_per_formula": 4,
                "phase_hints": ["DELAFOSSITE", "CUNIO2"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 2, "n_O2": 0.5,
            },
        ],
    },
    {
        "oxide": "CoO",
        "metal": "CO",
        "ternaries": [
            {
                "product": "CuCo2O4",
                "name": "copper cobaltite spinel",
                "reaction": "Cu + 2CoO + O2 -> CuCo2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["SPINEL"],
                "n_Cu": 1, "n_oxide_fu": 2, "oxide_atoms": 2, "n_O2": 1.0,
            },
        ],
    },
    {
        "oxide": "La2O3",
        "metal": "LA",
        "ternaries": [
            {
                "product": "CuLaO2",
                "name": "copper lanthanum oxide",
                "reaction": "Cu + 0.5 La2O3 + 0.25 O2 -> CuLaO2",
                "X_Cu": 1/4, "X_M": 1/4, "X_O": 2/4,
                "atoms_per_formula": 4,
                "phase_hints": ["DELAFOSSITE", "CULAO2"],
                "n_Cu": 1, "n_oxide_fu": 0.5, "oxide_atoms": 5, "n_O2": 0.25,
            },
        ],
    },
    {
        "oxide": "CeO2",
        "metal": "CE",
        "ternaries": [
            {
                "product": "CuCeO3",
                "name": "copper cerate (hypothetical)",
                "reaction": "Cu + CeO2 + 0.5 O2 -> CuCeO3",
                "X_Cu": 1/5, "X_M": 1/5, "X_O": 3/5,
                "atoms_per_formula": 5,
                "phase_hints": ["PEROVSKITE", "CUCEO3"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 3, "n_O2": 0.5,
            },
        ],
    },
    # B2O3 requires special handling (B may not coexist with Cu in TCOX14)
    {
        "oxide": "B2O3",
        "metal": "B",
        "ternaries": [
            {
                "product": "CuB2O4",
                "name": "copper borate",
                "reaction": "Cu + B2O3 + 0.5 O2 -> CuB2O4",
                "X_Cu": 1/7, "X_M": 2/7, "X_O": 4/7,
                "atoms_per_formula": 7,
                "phase_hints": ["BORATE", "CUBO", "CUB2O4"],
                "n_Cu": 1, "n_oxide_fu": 1, "oxide_atoms": 5, "n_O2": 0.5,
            },
        ],
    },
]

# PbO note: PB is not in TCOX14 (would need SSUB3 fallback).
# We skip PbO ternaries since Pb is toxic and not in TCOX14.


def find_phase_gm(result, phase_hints):
    """Search for a specific phase and return its GM value."""
    stable = result.get_stable_phases()
    for hint in phase_hints:
        for phase in stable:
            if hint.upper() in phase.upper():
                try:
                    gm = result.get_value_of(f"GM({phase})")
                    return gm, phase
                except Exception:
                    pass
    return None, None


def main():
    print("=" * 70)
    print("TC-Python: Ternary Reaction Energies (Cu + oxide -> complex)")
    print("=" * 70)
    print(f"Database: {DATABASE}")
    print(f"Temperature range: {T_MIN}-{T_MAX} K")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Started: {datetime.now().isoformat()}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temperatures = list(range(T_MIN, T_MAX + 1, T_STEP))

    # CSV rows
    all_rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        # =====================================================================
        # Step 1: Get Cu metal reference energy at each temperature
        # =====================================================================
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
                # Nearly pure Cu (tiny O to keep system defined)
                calc.set_condition(
                    ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                    0.0001
                )
                result = calc.calculate()
                G_Cu_metal[T] = result.get_value_of("GM")
            print(f"  Cu(metal) at 1500K: {G_Cu_metal.get(1500, 'N/A'):.1f} J/mol-atoms\n")
        except Exception as e:
            print(f"  ERROR getting Cu reference: {e}\n")
            return

        # =====================================================================
        # Step 2: Get O2 gas reference (per mol O2)
        # =====================================================================
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
            print(f"  O2(gas) at 1500K: {G_O2.get(1500, 'N/A'):.1f} J/mol-O2\n")
        except Exception as e:
            print(f"  ERROR getting O2 reference: {e}\n")
            return

        # =====================================================================
        # Step 3: For each ternary system, calculate product-side equilibrium
        # =====================================================================
        for sys_def in TERNARY_SYSTEMS:
            oxide_name = sys_def["oxide"]
            metal_el = sys_def["metal"]
            elements = ["CU", metal_el, "O"]

            print(f"\n{'='*60}")
            print(f"System: Cu-{metal_el}-O  (oxide = {oxide_name})")
            print(f"{'='*60}")

            # Try to set up this ternary system
            try:
                ternary_system = (session
                                  .select_database_and_elements(DATABASE, elements)
                                  .get_system())
            except Exception as e:
                print(f"  SYSTEM SETUP ERROR: {e}")
                print(f"  (Element {metal_el} may not be in {DATABASE})")
                # Write error rows
                for tern in sys_def["ternaries"]:
                    for T in temperatures:
                        all_rows.append({
                            "T_K": T,
                            "T_C": T - 273.15,
                            "oxide": oxide_name,
                            "product": tern["product"],
                            "product_name": tern["name"],
                            "reaction": tern["reaction"],
                            "GM_system_product": "",
                            "stable_phases": f"ERROR: {e}",
                            "ternary_phase_found": "",
                            "GM_ternary_phase": "",
                            "G_Cu_metal": "",
                            "G_O2": "",
                            "dG_rxn_system_J": "",
                            "dG_rxn_system_kJ": "",
                            "notes": f"Element {metal_el} not in {DATABASE}",
                        })
                continue

            # --- Also get the BINARY oxide reference in this ternary system ---
            # Calculate at the binary oxide stoichiometry (no Cu)
            print(f"  Getting {oxide_name} reference in ternary system...")
            G_binary_oxide = {}
            oxide_X_O_map = {
                "Al2O3": 3/5, "Cr2O3": 3/5, "La2O3": 3/5,
                "MnO": 1/2, "FeO": 1/2, "MgO": 1/2, "CaO": 1/2,
                "NiO": 1/2, "CoO": 1/2,
                "V2O5": 5/7, "TiO2": 2/3, "SiO2": 2/3, "ZrO2": 2/3,
                "CeO2": 2/3, "B2O3": 3/5,
            }
            oxide_atoms_map = {
                "Al2O3": 5, "Cr2O3": 5, "La2O3": 5,
                "MnO": 2, "FeO": 2, "MgO": 2, "CaO": 2,
                "NiO": 2, "CoO": 2,
                "V2O5": 7, "TiO2": 3, "SiO2": 3, "ZrO2": 3,
                "CeO2": 3, "B2O3": 5,
            }
            X_O_oxide = oxide_X_O_map.get(oxide_name, 0.5)
            atoms_oxide = oxide_atoms_map.get(oxide_name, 2)

            for T in temperatures:
                try:
                    calc = ternary_system.with_single_equilibrium_calculation()
                    calc.set_condition(ThermodynamicQuantity.temperature(), T)
                    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
                    # Set to binary oxide composition (X_Cu ~ 0)
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("CU"),
                        0.0001
                    )
                    calc.set_condition(
                        ThermodynamicQuantity.mole_fraction_of_a_component("O"),
                        X_O_oxide
                    )
                    result = calc.calculate()
                    G_binary_oxide[T] = result.get_value_of("GM")
                except Exception as e:
                    G_binary_oxide[T] = None

            if G_binary_oxide.get(1500):
                print(f"  {oxide_name} GM at 1500K: {G_binary_oxide[1500]:.1f} J/mol-atoms")

            # --- Now calculate at each TERNARY compound stoichiometry ---
            for tern in sys_def["ternaries"]:
                product = tern["product"]
                X_Cu = tern["X_Cu"]
                X_M = tern["X_M"]
                X_O = tern["X_O"]
                atoms = tern["atoms_per_formula"]
                phase_hints = tern["phase_hints"]

                print(f"\n  --- {product} ({tern['name']}) ---")
                print(f"  Composition: X_Cu={X_Cu:.4f}, X_{metal_el}={X_M:.4f}, X_O={X_O:.4f}")
                print(f"  Reaction: {tern['reaction']}")

                success = 0
                for T in temperatures:
                    row = {
                        "T_K": T,
                        "T_C": T - 273.15,
                        "oxide": oxide_name,
                        "product": product,
                        "product_name": tern["name"],
                        "reaction": tern["reaction"],
                    }

                    try:
                        calc = ternary_system.with_single_equilibrium_calculation()
                        calc.set_condition(ThermodynamicQuantity.temperature(), T)
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

                        # Look for ternary phase
                        gm_ternary, ternary_phase = find_phase_gm(result, phase_hints)

                        row["GM_system_product"] = GM_system
                        row["stable_phases"] = "; ".join(stable)
                        row["ternary_phase_found"] = ternary_phase if ternary_phase else ""
                        row["GM_ternary_phase"] = gm_ternary if gm_ternary else ""
                        row["G_Cu_metal"] = G_Cu_metal[T]
                        row["G_O2"] = G_O2[T]

                        # -------------------------------------------------
                        # Reaction dG calculation
                        #
                        # For the balanced reaction (e.g.):
                        #   Cu + Al2O3 + 0.5 O2 -> CuAl2O4
                        #
                        # G_products = GM_system * atoms_per_formula
                        #   (total G of 1 formula unit at this composition)
                        #
                        # G_reactants = n_Cu * G(Cu per atom)
                        #             + n_oxide_fu * oxide_atoms * G(oxide per atom)
                        #             + n_O2 * G(O2 per mol)
                        #
                        # dG_rxn = G_products - G_reactants
                        # If dG_rxn < 0, ternary compound formation
                        # is thermodynamically favorable.
                        # -------------------------------------------------

                        G_oxide_ref = G_binary_oxide.get(T)
                        if G_oxide_ref is not None:
                            n_Cu = tern["n_Cu"]
                            n_oxide_fu = tern["n_oxide_fu"]
                            ox_atoms = tern["oxide_atoms"]
                            n_O2 = tern["n_O2"]

                            # Product: system GM * total atoms in formula
                            G_products = GM_system * atoms

                            # Reactants: Cu metal + oxide + O2 gas
                            # G_Cu_metal is GM per atom of Cu
                            # G_oxide_ref is GM per atom of oxide
                            # G_O2 is already per mol O2
                            G_reactants = (n_Cu * G_Cu_metal[T]
                                           + n_oxide_fu * ox_atoms * G_oxide_ref
                                           + n_O2 * G_O2[T])

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
                        row["stable_phases"] = f"ERROR: {e}"
                        row["ternary_phase_found"] = ""
                        row["GM_ternary_phase"] = ""
                        row["G_Cu_metal"] = G_Cu_metal.get(T, "")
                        row["G_O2"] = G_O2.get(T, "")
                        row["dG_rxn_system_J"] = ""
                        row["dG_rxn_system_kJ"] = ""
                        row["notes"] = str(e)

                    all_rows.append(row)

                print(f"  Completed: {success}/{len(temperatures)} temperatures")

                # Print sample result at steelmaking temp
                sample_T = 1800
                sample_rows = [r for r in all_rows
                               if r["T_K"] == sample_T
                               and r["product"] == product
                               and r.get("dG_rxn_system_kJ")]
                if sample_rows:
                    sr = sample_rows[0]
                    dG = sr["dG_rxn_system_kJ"]
                    phases = sr["stable_phases"]
                    tern_found = sr["ternary_phase_found"]
                    verdict = "FAVORABLE (Cu captured)" if dG < 0 else "UNFAVORABLE"
                    print(f"  At 1800K: dG_rxn = {dG:+.1f} kJ/mol → {verdict}")
                    print(f"  Phases: {phases}")
                    if tern_found:
                        print(f"  Ternary phase: {tern_found}")

    # =========================================================================
    # Write CSV
    # =========================================================================
    fieldnames = [
        "T_K", "T_C", "oxide", "product", "product_name", "reaction",
        "GM_system_product", "stable_phases", "ternary_phase_found",
        "GM_ternary_phase", "G_Cu_metal", "G_O2",
        "dG_rxn_system_J", "dG_rxn_system_kJ", "notes",
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{'='*70}")
    print(f"CSV written to: {OUTPUT_FILE}")
    print(f"{len(all_rows)} rows ({len(TERNARY_SYSTEMS)} oxide systems)")
    print(f"Finished: {datetime.now().isoformat()}")
    print("=" * 70)

    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY: Ternary Reaction Feasibility at 1527°C (1800 K)")
    print("=" * 70)
    print(f"{'Product':<16} {'dG_rxn (kJ)':<14} {'Ternary Phase?':<20} {'Verdict':<16}")
    print("-" * 70)

    for sys_def in TERNARY_SYSTEMS:
        for tern in sys_def["ternaries"]:
            product = tern["product"]
            matches = [r for r in all_rows
                       if r["T_K"] == 1800 and r["product"] == product]
            if matches and matches[0].get("dG_rxn_system_kJ"):
                dG = matches[0]["dG_rxn_system_kJ"]
                phase = matches[0].get("ternary_phase_found", "")
                verdict = "FAVORABLE" if dG < 0 else "Unfavorable"
                print(f"{product:<16} {dG:>+10.1f}    {phase or 'not found':<20} {verdict:<16}")
            else:
                notes = matches[0].get("notes", "no data") if matches else "no data"
                print(f"{product:<16} {'N/A':>10}    {'--':<20} {notes:<16}")

    print("=" * 70)


if __name__ == "__main__":
    main()
