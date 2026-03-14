#!/usr/bin/env python3
"""
Quick probe: Can MOBOX be loaded alongside TCOX14 for oxide diffusion modeling?

Tests:
  1. Load TCOX14 alone -> single equilibrium (baseline)
  2. Load MOBOX1 with TCOX14 -> diffusion calc setup
  3. Load MOBOX2 with TCOX14 -> diffusion calc setup
  4. Try DICTRA-style calculation if any combination works

Run on OSU VM:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" check_mobox_tcox.py

Output: printed to terminal. Copy/paste results back.
"""

from datetime import datetime

print("=" * 70)
print("MOBOX + TCOX14 Compatibility Check")
print("Started: %s" % datetime.now().isoformat())
print("=" * 70)
print()

try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not available. Run on OSU VM.")
    raise SystemExit(1)

# Test elements for Cu-Fe-O system
ELEMENTS = ["CU", "FE", "O"]

results = []

with TCPython() as session:
    print("Connected to Thermo-Calc\n")

    # =========================================================================
    # Test 1: TCOX14 baseline (should work)
    # =========================================================================
    print("--- Test 1: TCOX14 alone (baseline) ---")
    try:
        system = (session
                  .select_database_and_elements("TCOX14", ELEMENTS)
                  .get_system())
        calc = system.with_single_equilibrium_calculation()
        calc.set_condition(ThermodynamicQuantity.temperature(), 1800)
        calc.set_condition(ThermodynamicQuantity.pressure(), 101325)
        calc.set_condition(
            ThermodynamicQuantity.mole_fraction_of_a_component("CU"), 0.1)
        calc.set_condition(
            ThermodynamicQuantity.mole_fraction_of_a_component("O"), 0.3)
        result = calc.calculate()
        a_Cu = result.get_value_of("AC(CU)")
        phases = result.get_stable_phases()
        print("  OK: a_Cu = %.6f" % a_Cu)
        print("  Stable phases: %s" % ", ".join(phases))
        results.append(("TCOX14 alone", "OK", "a_Cu=%.6f" % a_Cu))
    except Exception as e:
        print("  FAILED: %s" % str(e)[:100])
        results.append(("TCOX14 alone", "FAILED", str(e)[:80]))

    # =========================================================================
    # Test 2: Try loading MOBOX databases
    # =========================================================================
    for mob_db in ["MOBOX1", "MOBOX2"]:
        print()
        print("--- Test 2: %s database availability ---" % mob_db)

        # 2a: Can we even open the mobility database?
        try:
            # Try listing what's in the database
            print("  Attempting to access %s..." % mob_db)

            # Method 1: Try via diffusion calculation API
            try:
                diff_calc = (session
                             .select_thermodynamic_and_kinetic_databases_with_elements(
                                 "TCOX14", mob_db, ELEMENTS)
                             .get_system())
                print("  OK: %s loaded with TCOX14 via diffusion API!" % mob_db)
                print("  Available phases: %s" % ", ".join(
                    diff_calc.get_phase_names()[:10]))
                results.append(("%s+TCOX14 (diffusion)" % mob_db, "OK",
                               "loaded successfully"))

                # Try to set up a simple diffusion calculation
                print("  Attempting diffusion calculation setup...")
                try:
                    diff = diff_calc.with_diffusion_calculation()
                    print("  OK: Diffusion calculation object created!")
                    results.append(("%s diffusion calc" % mob_db, "OK",
                                   "calc object created"))
                except Exception as e2:
                    print("  Diffusion calc setup failed: %s" % str(e2)[:100])
                    results.append(("%s diffusion calc" % mob_db, "FAILED",
                                   str(e2)[:80]))

            except Exception as e:
                err_msg = str(e)[:150]
                print("  Diffusion API failed: %s" % err_msg)
                results.append(("%s+TCOX14 (diffusion)" % mob_db, "FAILED",
                               err_msg[:80]))

            # Method 2: Try loading as a standalone thermo database
            # (just to see if TC recognizes the name)
            try:
                test_sys = (session
                            .select_database_and_elements(mob_db, ELEMENTS)
                            .get_system())
                print("  %s loaded as thermo database (unexpected but ok)" % mob_db)
                phase_names = test_sys.get_phase_names()
                print("  Phases: %s" % ", ".join(phase_names[:10]))
                results.append(("%s as thermo" % mob_db, "OK",
                               "%d phases" % len(phase_names)))
            except Exception as e:
                print("  %s cannot load as thermo database: %s" % (
                    mob_db, str(e)[:80]))
                results.append(("%s as thermo" % mob_db, "EXPECTED_FAIL",
                               str(e)[:80]))

        except Exception as e:
            print("  OUTER ERROR with %s: %s" % (mob_db, str(e)[:100]))
            results.append((mob_db, "FAILED", str(e)[:80]))

    # =========================================================================
    # Test 3: Try MOBFE with TCOX14 (cross-database pairing)
    # =========================================================================
    print()
    print("--- Test 3: MOBFE9 + TCOX14 (cross-domain pairing) ---")
    for mob_db in ["MOBFE9", "MOBFE8", "MOBFE7"]:
        try:
            diff_sys = (session
                        .select_thermodynamic_and_kinetic_databases_with_elements(
                            "TCOX14", mob_db, ELEMENTS)
                        .get_system())
            print("  OK: %s + TCOX14 loaded!" % mob_db)
            results.append(("%s+TCOX14" % mob_db, "OK", "loaded"))
            break
        except Exception as e:
            print("  %s + TCOX14 failed: %s" % (mob_db, str(e)[:80]))
            results.append(("%s+TCOX14" % mob_db, "FAILED", str(e)[:80]))

    # =========================================================================
    # Test 4: Check what methods exist on the session for kinetics
    # =========================================================================
    print()
    print("--- Test 4: Available kinetic methods ---")
    kinetic_methods = [m for m in dir(session) if 'kinetic' in m.lower()
                       or 'diffus' in m.lower() or 'dictra' in m.lower()
                       or 'mobility' in m.lower()]
    if kinetic_methods:
        for m in kinetic_methods:
            print("  session.%s()" % m)
        results.append(("Kinetic methods", "FOUND", ", ".join(kinetic_methods)))
    else:
        print("  No kinetic/diffusion methods found on session object")
        results.append(("Kinetic methods", "NONE", ""))

    # Also check system-level methods
    try:
        system = (session
                  .select_database_and_elements("TCOX14", ELEMENTS)
                  .get_system())
        sys_methods = [m for m in dir(system) if 'diffus' in m.lower()
                       or 'kinetic' in m.lower()]
        if sys_methods:
            print("  System methods: %s" % ", ".join(sys_methods))
            results.append(("System kinetic methods", "FOUND",
                           ", ".join(sys_methods)))
    except Exception:
        pass

# =========================================================================
# Summary
# =========================================================================
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print("%-35s %-10s %s" % ("Test", "Status", "Details"))
print("-" * 70)
for test_name, status, details in results:
    print("%-35s %-10s %s" % (test_name, status, details[:40]))
print("=" * 70)
print("Finished: %s" % datetime.now().isoformat())
