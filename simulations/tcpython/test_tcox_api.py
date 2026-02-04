#!/usr/bin/env python3
"""
Test script to explore TC-Python API with TCOX14.
Run this to see what methods/properties are available.
"""

from tc_python import *

print("=" * 70)
print("TC-Python API Test (TCOX14)")
print("=" * 70)

with TCPython() as session:
    print("Connected.\n")

    # Create system
    print("Creating Cu-O system from TCOX14...")
    system = (session
        .select_database_and_elements("TCOX14", ["CU", "O"])
        .get_system())

    print(f"System type: {type(system)}")
    print(f"System methods: {[m for m in dir(system) if not m.startswith('_')]}\n")

    # Try single equilibrium
    print("Setting up equilibrium calculation...")
    calc = system.with_single_equilibrium_calculation()
    calc.set_condition(ThermodynamicQuantity.temperature(), 1273)  # 1000C
    calc.set_condition(ThermodynamicQuantity.pressure(), 101325)

    # Set composition for Cu2O (Cu:O = 2:1, so X(Cu)=0.667)
    calc.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component("O"), 0.333)

    print("Calculating...")
    result = calc.calculate()

    print(f"\nResult type: {type(result)}")
    print(f"Result methods: {[m for m in dir(result) if not m.startswith('_')]}\n")

    # Try to get various properties
    print("Attempting to read properties:")

    try:
        G = result.get_value_of("G")
        print(f"  G (total Gibbs): {G}")
    except Exception as e:
        print(f"  G: Error - {e}")

    try:
        GM = result.get_value_of("GM")
        print(f"  GM (Gibbs/mol): {GM}")
    except Exception as e:
        print(f"  GM: Error - {e}")

    try:
        phases = result.get_stable_phases()
        print(f"  Stable phases: {phases}")
    except Exception as e:
        print(f"  Stable phases: Error - {e}")

    try:
        # Try getting Gibbs of specific phase
        G_cu2o = result.get_value_of("G(CU2O)")
        print(f"  G(CU2O): {G_cu2o}")
    except Exception as e:
        print(f"  G(CU2O): Error - {e}")

    try:
        G_cupriteA = result.get_value_of("G(CUPRITE_A)")
        print(f"  G(CUPRITE_A): {G_cupriteA}")
    except Exception as e:
        print(f"  G(CUPRITE_A): Error - {e}")

print("\n" + "=" * 70)
print("Test complete.")
print("=" * 70)
