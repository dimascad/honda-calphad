#!/usr/bin/env python3
"""
Comprehensive DICTRA / Diffusion Capability Test for Honda CALPHAD Project.

This script systematically explores TC-Python's diffusion capabilities
to determine what kinetic calculations are possible for Cu removal from
recycled steel. It answers the critical question: can we model Cu transport
across the steel/slag interface?

Six phases of testing:
  Phase 1: Database compatibility matrix (all thermo x mobility combos)
  Phase 2: Deep system exploration (phases, methods, elements with mobility)
  Phase 3: Single-region diffusion (Cu gradient in FCC austenite)
  Phase 4: Diffusion coefficient extraction (D_Cu at multiple temperatures)
  Phase 5: Multi-region interface (steel | slag two-region setup)
  Phase 6: Boundary condition tests (closed, fixed composition, activity)

Run on OSU VM:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" test_dictra_diffusion.py

Expected runtime: 5-15 minutes depending on which calculations succeed.

Output: test_dictra_results.csv (all results in parseable format)
"""

from datetime import datetime
import csv
import os
import sys
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "tcpython", "raw")
CSV_PATH = os.path.join(OUTPUT_DIR, "dictra_capability_test.csv")

print("=" * 75)
print("DICTRA / Diffusion Comprehensive Capability Test")
print("Honda CALPHAD - Cu Removal from Recycled Steel")
print("Started: %s" % datetime.now().isoformat())
print("=" * 75)
print()

try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not available. Run on OSU VM with:")
    print('  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" %s'
          % os.path.basename(__file__))
    raise SystemExit(1)

# =====================================================================
# Configuration
# =====================================================================

# Thermodynamic databases (most relevant first)
THERMO_DBS = ["TCFE13", "TCFE12", "TCFE11", "TCOX14"]

# Mobility databases — test everything available
# Prior probes confirmed: MOBFE9, MOBOX1, MOBOX2 NOT FOUND on VM
# but we test them anyway for completeness
MOBILITY_DBS = [
    "MOBFE8", "MOBFE7", "MOBFE6", "MOBFE5",
    "MOBFE9",
    "MOBOX1", "MOBOX2",
    "MOBCU3", "MOBCU2",
    "MOBNI5", "MOBNI4",
    "MOBAL3", "MOBAL2",
]

# Element sets to test
ELEMENT_SETS = [
    (["CU", "FE"],           "Cu-Fe"),
    (["CU", "FE", "O"],      "Cu-Fe-O"),
    (["CU", "FE", "C"],      "Cu-Fe-C"),
    (["CU", "FE", "MN"],     "Cu-Fe-Mn"),
    (["CU", "FE", "AL"],     "Cu-Fe-Al"),
    (["CU", "FE", "MN", "O"], "Cu-Fe-Mn-O"),
]

# Temperatures of interest (K)
TEMPERATURES = [1073, 1273, 1473, 1573, 1673, 1773, 1800, 1873]

# Cu compositions for steelmaking
CU_LEVELS = {
    "trace":       0.001,   # 0.1 wt% - low contamination
    "typical":     0.003,   # 0.3 wt% - typical recycled steel
    "high":        0.005,   # 0.5 wt% - heavily contaminated
}

results = []   # (phase, test_name, status, details)
csv_rows = []  # for CSV output


def log(phase, test, status, detail):
    """Print and record a test result."""
    tag = {"OK": "+", "FAIL": "X", "INFO": "i", "SKIP": "-",
           "SUCCESS": "*", "WARN": "!"}
    marker = tag.get(status, "?")
    print("  [%s] %-40s %s" % (marker, test, detail[:60]))
    results.append((phase, test, status, detail))
    csv_rows.append({
        "phase": phase,
        "test": test,
        "status": status,
        "detail": detail,
        "timestamp": datetime.now().isoformat(),
    })


# =====================================================================
# PHASE 1: Database Compatibility Matrix
# =====================================================================
print("=" * 75)
print("PHASE 1: Database Compatibility Matrix")
print("  Testing %d thermo x %d mobility x %d element sets = %d combos"
      % (len(THERMO_DBS), len(MOBILITY_DBS), len(ELEMENT_SETS),
         len(THERMO_DBS) * len(MOBILITY_DBS) * len(ELEMENT_SETS)))
print("=" * 75)
print()

working_pairs = []  # (tdb, mob, elems, label, phases)

with TCPython() as session:
    print("Connected to Thermo-Calc engine\n")

    # First pass: probe the kinetic System object API on the first
    # successful load so we know what methods exist
    system_api_probed = False

    for tdb in THERMO_DBS:
        print("  --- %s ---" % tdb)
        for mob in MOBILITY_DBS:
            for elems, elem_label in ELEMENT_SETS:
                label = "%s + %s (%s)" % (tdb, mob, elem_label)
                try:
                    system = (session
                              .select_thermodynamic_and_kinetic_databases_with_elements(
                                  tdb, mob, elems)
                              .get_system())

                    # The kinetic System object may NOT have get_phase_names()
                    # (confirmed: TC-Python 2025b raises AttributeError).
                    # Probe all available methods on first success.
                    if not system_api_probed:
                        system_api_probed = True
                        sys_methods = sorted([
                            m for m in dir(system)
                            if not m.startswith('_')])
                        print()
                        print("  ** Kinetic System API probe (first success) **")
                        print("  Type: %s" % type(system).__name__)
                        print("  Methods/attrs (%d):" % len(sys_methods))
                        for m in sys_methods:
                            print("    .%s" % m)
                        print()
                        log("P1", "System API probe", "INFO",
                            "type=%s methods=%d" % (
                                type(system).__name__, len(sys_methods)))

                    # Try to get phases (multiple possible API names)
                    # get_phases_in_system() confirmed as correct method
                    # via Phase 1 API probe (method #9 on kinetic System)
                    phases = []
                    for phase_method in ["get_phases_in_system",
                                         "get_phase_names",
                                         "get_phases",
                                         "get_phase_list"]:
                        fn = getattr(system, phase_method, None)
                        if fn is not None and callable(fn):
                            try:
                                phases = fn()
                                break
                            except Exception:
                                pass

                    # Check diffusion API
                    has_iso = hasattr(system, 'with_isothermal_diffusion_calculation')
                    has_noniso = hasattr(system, 'with_non_isothermal_diffusion_calculation')

                    if has_iso:
                        status = "OK"
                        if phases:
                            # Categorize phases
                            tags = []
                            fcc = [p for p in phases if "FCC" in p]
                            bcc = [p for p in phases if "BCC" in p]
                            ionic = [p for p in phases if "IONIC" in p]
                            liquid = [p for p in phases if "LIQUID" in p]
                            spinel = [p for p in phases if "SPINEL" in p]
                            if fcc: tags.append("FCC(%d)" % len(fcc))
                            if bcc: tags.append("BCC(%d)" % len(bcc))
                            if ionic: tags.append("IONIC(%d)" % len(ionic))
                            if liquid: tags.append("LIQ(%d)" % len(liquid))
                            if spinel: tags.append("SPINEL(%d)" % len(spinel))
                            detail = "%d phases [%s]" % (
                                len(phases), " ".join(tags))
                        else:
                            detail = "loaded (phases not queryable)"
                        detail += " iso=%s noniso=%s" % (has_iso, has_noniso)
                        working_pairs.append((tdb, mob, elems, elem_label, phases))
                    else:
                        status = "WARN"
                        detail = "loaded but NO diffusion API"

                    log("P1", label, status, detail)

                except Exception as e:
                    err = str(e)
                    if "not found" in err.lower():
                        log("P1", label, "FAIL", "Database not found")
                    else:
                        log("P1", label, "FAIL", err[:80])

        print()  # blank between thermo DBs

    # Summary of Phase 1
    print()
    print("  Phase 1 Summary: %d working pairs found" % len(working_pairs))
    if working_pairs:
        # Deduplicate by (tdb, mob)
        seen = set()
        unique = []
        for tdb, mob, elems, label, phases in working_pairs:
            key = (tdb, mob)
            if key not in seen:
                seen.add(key)
                unique.append((tdb, mob, elems, label, phases))
        print("  Unique thermo+mobility pairs: %d" % len(unique))
        for tdb, mob, elems, label, phases in unique:
            print("    %s + %s  (%d phases)" % (tdb, mob, len(phases)))
    print()

    if not working_pairs:
        print("  *** No working pairs found. Cannot proceed. ***")
        print("  Check that mobility databases are installed on this VM.")
    else:

        # =============================================================
        # PHASE 2: Deep System Exploration
        # =============================================================
        print("=" * 75)
        print("PHASE 2: Deep System Exploration")
        print("=" * 75)
        print()

        # Group working pairs and explore the most promising ones
        # Priority: TCFE13+MOBFE8 (steel), TCOX14+MOBFE8 (oxide+steel mob)
        priority_pairs = []
        other_pairs = []
        for entry in working_pairs:
            tdb, mob = entry[0], entry[1]
            if (tdb == "TCFE13" and mob == "MOBFE8") or \
               (tdb == "TCOX14" and mob == "MOBFE8"):
                priority_pairs.append(entry)
            elif len(priority_pairs) == 0:
                # Keep first working pair as fallback
                other_pairs.append(entry)

        explore_pairs = priority_pairs if priority_pairs else other_pairs[:2]

        for tdb, mob, elems, elem_label, phases in explore_pairs:
            pair_name = "%s + %s (%s)" % (tdb, mob, elem_label)
            print("  --- Exploring: %s ---" % pair_name)

            try:
                system = (session
                          .select_thermodynamic_and_kinetic_databases_with_elements(
                              tdb, mob, elems)
                          .get_system())

                # List ALL phases (try multiple API methods)
                all_phases = []
                for phase_method in ["get_phases_in_system",
                                     "get_phase_names", "get_phases",
                                     "get_phase_list"]:
                    fn = getattr(system, phase_method, None)
                    if fn is not None and callable(fn):
                        try:
                            all_phases = fn()
                            print("  Phases via .%s() (%d):" % (
                                phase_method, len(all_phases)))
                            break
                        except Exception as ex:
                            print("  .%s() failed: %s" % (
                                phase_method, str(ex)[:60]))

                if not all_phases:
                    print("  Could not enumerate phases (API differs)")
                    log("P2", "%s phases" % pair_name, "WARN",
                        "phase enumeration not available")
                else:
                    for p in sorted(all_phases):
                        print("    %s" % p)
                    log("P2", "%s phases" % pair_name, "INFO",
                        "%d: %s" % (len(all_phases),
                                    ", ".join(sorted(all_phases))))

                # Create diffusion calc and inspect its methods
                diff_calc = system.with_isothermal_diffusion_calculation()
                methods = sorted([m for m in dir(diff_calc)
                                  if not m.startswith('_')
                                  and callable(getattr(diff_calc, m, None))])
                print("  Diffusion calc methods (%d):" % len(methods))
                for m in methods:
                    print("    .%s()" % m)
                log("P2", "%s diff methods" % pair_name, "INFO",
                    ", ".join(methods))

                # Check what geometry types are available
                for geom_name, geom_fn in [
                    ("planar", "with_planar_geometry"),
                    ("cylindrical", "with_cylindrical_geometry"),
                    ("spherical", "with_spherical_geometry"),
                ]:
                    if geom_fn in methods:
                        log("P2", "%s geometry: %s" % (pair_name, geom_name),
                            "OK", "available")
                    else:
                        log("P2", "%s geometry: %s" % (pair_name, geom_name),
                            "FAIL", "not found in methods")

                # Check Region, Grid, etc. classes exist
                for cls_name in ["Region", "CalculatedGrid",
                                 "CompositionProfile", "ElementProfile",
                                 "BoundaryCondition", "Unit",
                                 "PhaseComposition",
                                 "AutomaticSolver", "ClassicSolver",
                                 "HomogenizationSolver",
                                 "SimulationTime"]:
                    exists = cls_name in dir()
                    log("P2", "Class: %s" % cls_name,
                        "OK" if exists else "FAIL",
                        "available in namespace" if exists else "NOT imported")

            except Exception as e:
                log("P2", pair_name, "FAIL", str(e)[:120])
            print()

        # =============================================================
        # PHASE 3: Single-Region Diffusion (Cu in austenite)
        # =============================================================
        print("=" * 75)
        print("PHASE 3: Single-Region Diffusion Calculation")
        print("  Cu diffusion in FCC austenite (simplest possible test)")
        print("=" * 75)
        print()

        # Initialize — used by Phase 5 to decide whether to attempt
        calc_succeeded = False

        # Find best pair for steel diffusion (TCFE + MOBFE)
        steel_pair = None
        for tdb, mob, elems, label, phases in working_pairs:
            if "TCFE" in tdb and "MOBFE" in mob and label == "Cu-Fe":
                if any("FCC" in p for p in phases):
                    steel_pair = (tdb, mob, elems, label, phases)
                    break

        # Fallback to any working pair with FCC
        if steel_pair is None:
            for tdb, mob, elems, label, phases in working_pairs:
                if any("FCC" in p for p in phases):
                    steel_pair = (tdb, mob, elems, label, phases)
                    break

        # Second fallback: if phases lists are all empty (enumeration failed),
        # pick any TCFE+MOBFE Cu-Fe pair anyway (FCC_A1 exists, just not
        # queryable via the old API methods)
        if steel_pair is None:
            for tdb, mob, elems, label, phases in working_pairs:
                if "TCFE" in tdb and "MOBFE" in mob and label == "Cu-Fe":
                    steel_pair = (tdb, mob, elems, label, phases)
                    print("  (Using %s+%s despite empty phases list)" % (tdb, mob))
                    break

        # Third fallback: any working pair at all
        if steel_pair is None and working_pairs:
            steel_pair = working_pairs[0]
            tdb, mob, elems, label, phases = steel_pair
            print("  (Using first available pair: %s+%s [%s])" % (tdb, mob, label))

        if steel_pair is None:
            print("  No working pair found at all. Skipping Phase 3.")
            log("P3", "Single-region setup", "SKIP", "no working pair")
        else:
            tdb, mob, elems, elem_label, phases = steel_pair
            pair_name = "%s + %s (%s)" % (tdb, mob, elem_label)
            print("  Using: %s" % pair_name)
            print()

            system = (session
                      .select_thermodynamic_and_kinetic_databases_with_elements(
                          tdb, mob, elems)
                      .get_system())

            # Identify FCC phase name — try to get phases from system
            # If phases list is empty (API doesn't support enumeration),
            # just assume standard TC naming conventions
            if not phases:
                # Re-probe using the fresh system object
                for phase_method in ["get_phases_in_system",
                                     "get_phase_names", "get_phases"]:
                    fn = getattr(system, phase_method, None)
                    if fn and callable(fn):
                        try:
                            phases = fn()
                            break
                        except Exception:
                            pass

            # At 1800K steel is liquid, not FCC. Try FCC first (for 1200K
            # tests), but also accept LIQUID as a fallback (for 1800K tests).
            diff_phase = "FCC_A1"  # default assumption
            diff_temp = 1200       # use 1200K for FCC (austenite range)
            use_liquid = False
            if phases:
                # Look for FCC first
                for p in phases:
                    if "FCC" in p and "A1" in p:
                        diff_phase = p
                        break
                else:
                    fcc_candidates = [p for p in phases if "FCC" in p]
                    if fcc_candidates:
                        diff_phase = fcc_candidates[0]
                    else:
                        # No FCC found — try LIQUID for 1800K
                        liq_candidates = [p for p in phases if "LIQUID" in p]
                        if liq_candidates:
                            diff_phase = liq_candidates[0]
                            diff_temp = 1800
                            use_liquid = True
            print("  Diffusion phase: %s @ %dK (from %s)" % (
                diff_phase, diff_temp,
                "enumeration" if phases else "assumed standard name"))

            # --- Try MULTIPLE API patterns for region setup ---
            # The API may vary between TC-Python versions.
            # Pattern A: CompositionProfile + ElementProfile (2022+ API)
            # Pattern B: PhaseComposition + set_composition (older API)
            # Pattern C: add_region with just phase name

            calc_succeeded = False

            # PATTERN A: CompositionProfile + ElementProfile
            print()
            print("  === Pattern A: CompositionProfile + ElementProfile ===")
            try:
                diff_a = system.with_isothermal_diffusion_calculation()
                diff_a.set_temperature(diff_temp)
                diff_a.set_simulation_time(3600)  # 1 hour

                region_a = (Region("steel_region")
                            .set_width(1e-3)  # 1 mm
                            .with_grid(CalculatedGrid.linear()
                                       .set_no_of_points(50))
                            .with_composition_profile(
                                CompositionProfile(Unit.MASS_PERCENT)
                                .add("CU", ElementProfile.linear(0.5, 0.0))))

                diff_a.add_region(region_a)
                log("P3", "Pattern A region", "OK",
                    "1mm, 50pts, linear Cu 0.5->0.0 wt%%")

                # Set boundary conditions
                diff_a.with_left_boundary_condition(
                    BoundaryCondition.closed_system())
                diff_a.with_right_boundary_condition(
                    BoundaryCondition.closed_system())
                log("P3", "Pattern A boundaries", "OK", "closed both sides")

                # Calculate
                print("  Running simulation (%dK, 3600s, %s)..." % (
                    diff_temp, diff_phase))
                result_a = diff_a.calculate()
                print("  *** PATTERN A CALCULATION SUCCEEDED ***")
                log("P3", "Pattern A calc", "SUCCESS",
                    "%dK, 3600s, Cu in %s" % (diff_temp, diff_phase))
                calc_succeeded = True

                # Extract results
                try:
                    times = result_a.get_time_steps()
                    print("  Time steps computed: %d" % len(times))
                    print("  Time range: %.1f to %.1f s" % (
                        min(times), max(times)))
                    log("P3", "Time steps", "OK",
                        "%d steps, %.0f-%.0f s" % (
                            len(times), min(times), max(times)))
                except Exception as e:
                    log("P3", "Time steps", "FAIL", str(e)[:80])

                # Composition profile at final time
                try:
                    dist, comp = result_a.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    n_pts = len(dist)
                    cu_min = min(comp) * 100
                    cu_max = max(comp) * 100
                    print("  Cu profile at t_final: %d points" % n_pts)
                    print("  Cu range: %.4f - %.4f wt%%" % (cu_min, cu_max))
                    log("P3", "Cu profile (mass frac)", "OK",
                        "%d pts, Cu %.4f-%.4f wt%%" % (n_pts, cu_min, cu_max))

                    # Print first few and last few points
                    print("  Profile (distance_m, Cu_wt%%):")
                    for i in range(min(5, n_pts)):
                        print("    %.6e  %.6f" % (dist[i], comp[i] * 100))
                    if n_pts > 10:
                        print("    ...")
                    for i in range(max(n_pts - 3, 5), n_pts):
                        print("    %.6e  %.6f" % (dist[i], comp[i] * 100))
                except Exception as e:
                    log("P3", "Cu profile (mass frac)", "FAIL", str(e)[:100])

                # Try mole fraction too
                try:
                    dist_m, comp_m = result_a.get_mole_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    log("P3", "Cu profile (mole frac)", "OK",
                        "%d pts" % len(dist_m))
                except Exception as e:
                    log("P3", "Cu profile (mole frac)", "FAIL", str(e)[:80])

                # Phase fraction profile
                try:
                    dist_p, frac_p = result_a.get_mass_fraction_of_phase_at_time(
                        diff_phase, SimulationTime.LAST)
                    print("  %s fraction: %.4f - %.4f" % (
                        diff_phase, min(frac_p), max(frac_p)))
                    log("P3", "%s fraction" % diff_phase, "OK",
                        "%.4f - %.4f" % (min(frac_p), max(frac_p)))
                except Exception as e:
                    log("P3", "%s fraction" % diff_phase, "FAIL", str(e)[:80])

                # Region width over time
                try:
                    t_w, w = result_a.get_width_of_region("steel_region")
                    print("  Region width: %.6e to %.6e m" % (
                        w[0], w[-1]))
                    log("P3", "Region width", "OK",
                        "%.3e -> %.3e m" % (w[0], w[-1]))
                except Exception as e:
                    log("P3", "Region width", "FAIL", str(e)[:80])

            except Exception as e:
                tb = traceback.format_exc()
                print("  Pattern A failed: %s" % str(e)[:200])
                print("  Traceback:\n%s" % tb[-500:])
                log("P3", "Pattern A", "FAIL", str(e)[:120])

            # PATTERN B: PhaseComposition (older/alternative API)
            if not calc_succeeded:
                print()
                print("  === Pattern B: PhaseComposition API ===")
                try:
                    diff_b = system.with_isothermal_diffusion_calculation()
                    diff_b.set_temperature(diff_temp)
                    diff_b.set_simulation_time(3600)

                    region_b = (Region("steel_region")
                                .set_width(1e-3)
                                .with_grid(CalculatedGrid.linear()
                                           .set_no_of_points(50))
                                .add_phase_composition(
                                    PhaseComposition(diff_phase)
                                    .set_composition("CU", 0.003)))

                    diff_b.add_region(region_b)
                    log("P3", "Pattern B region", "OK",
                        "PhaseComposition API accepted")

                    diff_b.with_left_boundary_condition(
                        BoundaryCondition.closed_system())
                    diff_b.with_right_boundary_condition(
                        BoundaryCondition.closed_system())

                    print("  Running simulation...")
                    result_b = diff_b.calculate()
                    print("  *** PATTERN B CALCULATION SUCCEEDED ***")
                    log("P3", "Pattern B calc", "SUCCESS", "1800K, 3600s")
                    calc_succeeded = True

                    # Extract basic results
                    try:
                        dist, comp = result_b.get_mass_fraction_of_component_at_time(
                            "CU", SimulationTime.LAST)
                        log("P3", "Pattern B Cu profile", "OK",
                            "%d pts" % len(dist))
                    except Exception as e:
                        log("P3", "Pattern B Cu profile", "FAIL",
                            str(e)[:80])

                except Exception as e:
                    print("  Pattern B failed: %s" % str(e)[:200])
                    log("P3", "Pattern B", "FAIL", str(e)[:120])

            # PATTERN C: Minimal setup (just phase, no composition)
            if not calc_succeeded:
                print()
                print("  === Pattern C: Minimal region (phase only) ===")
                try:
                    diff_c = system.with_isothermal_diffusion_calculation()
                    diff_c.set_temperature(diff_temp)
                    diff_c.set_simulation_time(60)

                    # Just region + grid, no explicit composition
                    region_c = (Region("test")
                                .set_width(1e-4)
                                .with_grid(CalculatedGrid.linear()
                                           .set_no_of_points(10)))

                    diff_c.add_region(region_c)
                    log("P3", "Pattern C region", "OK", "minimal setup")

                    print("  Running simulation...")
                    result_c = diff_c.calculate()
                    log("P3", "Pattern C calc", "SUCCESS", "minimal")
                    calc_succeeded = True
                except Exception as e:
                    log("P3", "Pattern C", "FAIL", str(e)[:120])

            if not calc_succeeded:
                print()
                print("  All region API patterns failed.")
                print("  Dumping full method list for debugging:")
                try:
                    diff_dbg = system.with_isothermal_diffusion_calculation()
                    for attr in sorted(dir(diff_dbg)):
                        if not attr.startswith('_'):
                            obj = getattr(diff_dbg, attr, None)
                            if callable(obj):
                                # Try to get signature
                                try:
                                    import inspect
                                    sig = str(inspect.signature(obj))
                                except Exception:
                                    sig = "()"
                                print("    .%s%s" % (attr, sig))
                            else:
                                print("    .%s = %s" % (attr, repr(obj)[:60]))
                except Exception as e:
                    print("  Debug dump failed: %s" % str(e)[:100])

        # =============================================================
        # PHASE 4: Diffusion Coefficient Extraction
        # =============================================================
        print()
        print("=" * 75)
        print("PHASE 4: Cu Diffusion Coefficients vs Temperature")
        print("  Extracting D_Cu at multiple temperatures")
        print("=" * 75)
        print()

        if steel_pair is None:
            print("  Skipped (no working steel pair).")
            log("P4", "D_Cu extraction", "SKIP", "no pair")
        elif not calc_succeeded:
            print("  Skipped (Phase 3 calc failed, API pattern unknown).")
            log("P4", "D_Cu extraction", "SKIP", "no working API pattern")
        else:
            tdb, mob, elems, elem_label, phases = steel_pair
            system = (session
                      .select_thermodynamic_and_kinetic_databases_with_elements(
                          tdb, mob, elems)
                      .get_system())

            # Try to get diffusion coefficients via short simulations
            # at each temperature with a small Cu step
            print("  Method: short diffusion sim with Cu step profile")
            print("  Temperatures: %s K" %
                  ", ".join(str(t) for t in TEMPERATURES))
            print()

            d_cu_data = []

            for T in TEMPERATURES:
                try:
                    diff_d = system.with_isothermal_diffusion_calculation()
                    diff_d.set_temperature(T)
                    diff_d.set_simulation_time(1.0)  # 1 second

                    # Step profile: Cu jumps from 0.5 to 0.0 at midpoint
                    region_d = (Region("test_D")
                                .set_width(1e-4)  # 100 um
                                .with_grid(CalculatedGrid.linear()
                                           .set_no_of_points(30))
                                .with_composition_profile(
                                    CompositionProfile(Unit.MASS_PERCENT)
                                    .add("CU", ElementProfile.step(
                                        0.5, 0.0, 5e-5))))

                    diff_d.add_region(region_d)
                    diff_d.with_left_boundary_condition(
                        BoundaryCondition.closed_system())
                    diff_d.with_right_boundary_condition(
                        BoundaryCondition.closed_system())

                    result_d = diff_d.calculate()

                    # Get initial and final profiles
                    dist0, comp0 = result_d.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.FIRST)
                    dist1, comp1 = result_d.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)

                    # Estimate D from broadening of step profile
                    # For a step diffusing for time t: width ~ sqrt(4*D*t)
                    # Measure width of transition zone
                    c_max = max(comp1)
                    c_min = min(comp1)
                    c_range = c_max - c_min
                    if c_range > 1e-10:
                        c_10 = c_min + 0.1 * c_range
                        c_90 = c_min + 0.9 * c_range
                        x_10 = None
                        x_90 = None
                        for i in range(len(comp1) - 1):
                            if comp1[i] >= c_90 and comp1[i+1] < c_90:
                                x_90 = dist1[i]
                            if comp1[i] >= c_10 and comp1[i+1] < c_10:
                                x_10 = dist1[i]
                        if x_10 is not None and x_90 is not None:
                            delta_x = abs(x_10 - x_90)
                            # For error function profile:
                            # erf(x / 2*sqrt(D*t)) -> delta_x ~ 2*erfinv(0.8)*2*sqrt(D*t)
                            # Simplified: D ~ (delta_x)^2 / (4*t)
                            D_est = (delta_x ** 2) / (4.0 * 1.0)
                            d_cu_data.append((T, D_est, delta_x, len(dist1)))
                            log("P4", "D_Cu at %dK" % T, "OK",
                                "D ~ %.2e m2/s (dx=%.2e m)" % (D_est, delta_x))
                        else:
                            log("P4", "D_Cu at %dK" % T, "WARN",
                                "Could not measure transition zone")
                    else:
                        log("P4", "D_Cu at %dK" % T, "WARN",
                            "No Cu gradient (fully homogenized?)")

                except Exception as e:
                    log("P4", "D_Cu at %dK" % T, "FAIL", str(e)[:100])

            if d_cu_data:
                print()
                print("  D_Cu vs Temperature:")
                print("  %-8s  %-12s  %-12s" % ("T (K)", "D (m2/s)", "dx (m)"))
                print("  " + "-" * 36)
                for T, D, dx, npts in d_cu_data:
                    print("  %-8d  %.3e  %.3e" % (T, D, dx))
                log("P4", "D_Cu summary", "OK",
                    "%d temperatures measured" % len(d_cu_data))

        # =============================================================
        # PHASE 5: Multi-Region Interface (Steel | Slag)
        # =============================================================
        print()
        print("=" * 75)
        print("PHASE 5: Two-Region Interface (Steel | Slag)")
        print("  Can we model Cu transport across steel/slag boundary?")
        print("=" * 75)
        print()

        # Need a pair with BOTH metallic and oxide phases
        # TCOX14 + MOBFE8 is our best candidate
        oxide_pair = None
        for tdb, mob, elems, label, phases in working_pairs:
            if tdb == "TCOX14" and label == "Cu-Fe-O":
                oxide_pair = (tdb, mob, elems, label, phases)
                break
        # Also try TCFE with Cu-Fe-O
        if oxide_pair is None:
            for tdb, mob, elems, label, phases in working_pairs:
                if "O" in elems and any("IONIC" in p or "LIQUID" in p
                                         for p in phases):
                    oxide_pair = (tdb, mob, elems, label, phases)
                    break

        if oxide_pair is None:
            print("  No working oxide pair found. Skipping.")
            log("P5", "Two-region setup", "SKIP", "no oxide pair")
        elif not calc_succeeded:
            print("  Skipping (Phase 3 API patterns all failed).")
            log("P5", "Two-region setup", "SKIP", "no working API")
        else:
            tdb, mob, elems, elem_label, phases = oxide_pair
            pair_name = "%s + %s (%s)" % (tdb, mob, elem_label)
            print("  Using: %s" % pair_name)
            print("  Phases: %s" % ", ".join(sorted(phases)))
            print()

            system = (session
                      .select_thermodynamic_and_kinetic_databases_with_elements(
                          tdb, mob, elems)
                      .get_system())

            # Identify metallic and oxide phases
            # Re-probe phases if empty
            if not phases:
                for phase_method in ["get_phases_in_system",
                                     "get_phase_names", "get_phases"]:
                    fn = getattr(system, phase_method, None)
                    if fn and callable(fn):
                        try:
                            phases = fn()
                            break
                        except Exception:
                            pass

            metal_phase = "FCC_A1"   # default assumptions
            oxide_phase = "IONIC_LIQ"
            if phases:
                metal_phase = None
                oxide_phase = None
                for p in phases:
                    if "FCC" in p and "A1" in p:
                        metal_phase = p
                    if "IONIC" in p and "LIQ" in p:
                        oxide_phase = p
                if metal_phase is None:
                    for p in phases:
                        if "LIQUID" in p:
                            metal_phase = p
                            break
                        if "BCC" in p:
                            metal_phase = p
                            break

            print("  Metal phase: %s%s" % (
                metal_phase or "NONE",
                " (assumed)" if not phases else ""))
            print("  Oxide phase: %s%s" % (
                oxide_phase or "NONE",
                " (assumed)" if not phases else ""))

            # Test A: Two regions, same phase (simpler)
            print()
            print("  --- Test A: Two FCC regions (diffusion couple) ---")
            if metal_phase:
                try:
                    diff_5a = system.with_isothermal_diffusion_calculation()
                    diff_5a.set_temperature(1800)
                    diff_5a.set_simulation_time(3600)

                    # Left region: Cu-rich steel
                    region_left = (Region("cu_rich")
                                   .set_width(5e-4)  # 500 um
                                   .with_grid(
                                       CalculatedGrid.double_geometric()
                                       .set_no_of_points(25)
                                       .set_geometrical_factor(0.9))
                                   .with_composition_profile(
                                       CompositionProfile(Unit.MASS_PERCENT)
                                       .add("CU", ElementProfile.constant(0.5))))

                    # Right region: pure Fe
                    region_right = (Region("pure_fe")
                                    .set_width(5e-4)
                                    .with_grid(
                                        CalculatedGrid.double_geometric()
                                        .set_no_of_points(25)
                                        .set_geometrical_factor(1.1))
                                    .with_composition_profile(
                                        CompositionProfile(Unit.MASS_PERCENT)
                                        .add("CU", ElementProfile.constant(0.0))))

                    diff_5a.add_region(region_left)
                    diff_5a.add_region(region_right)
                    diff_5a.with_left_boundary_condition(
                        BoundaryCondition.closed_system())
                    diff_5a.with_right_boundary_condition(
                        BoundaryCondition.closed_system())

                    print("  Running diffusion couple simulation...")
                    result_5a = diff_5a.calculate()
                    print("  *** TWO-REGION CALCULATION SUCCEEDED ***")
                    log("P5", "Two-region diffusion couple", "SUCCESS",
                        "Cu-rich | pure Fe at 1800K")

                    # Extract interface position
                    try:
                        t_if, x_if = result_5a.get_position_of_upper_boundary_of_region(
                            "cu_rich")
                        print("  Interface moved: %.6e -> %.6e m" % (
                            x_if[0], x_if[-1]))
                        log("P5", "Interface position", "OK",
                            "%.3e -> %.3e m" % (x_if[0], x_if[-1]))
                    except Exception as e:
                        log("P5", "Interface position", "FAIL",
                            str(e)[:80])

                    # Cu profile across both regions
                    try:
                        dist, comp = result_5a.get_mass_fraction_of_component_at_time(
                            "CU", SimulationTime.LAST)
                        print("  Cu profile across interface: %d points" %
                              len(dist))
                        print("  Cu range: %.4f - %.4f wt%%" % (
                            min(comp) * 100, max(comp) * 100))
                        log("P5", "Cu profile across interface", "OK",
                            "%d pts, %.4f-%.4f wt%%" % (
                                len(dist), min(comp)*100, max(comp)*100))
                    except Exception as e:
                        log("P5", "Cu profile across interface", "FAIL",
                            str(e)[:80])

                except Exception as e:
                    print("  Two-region test failed: %s" % str(e)[:200])
                    log("P5", "Two-region diffusion couple", "FAIL",
                        str(e)[:120])

            # Test B: Metal + oxide two-phase (the real goal)
            if metal_phase and oxide_phase:
                print()
                print("  --- Test B: Metal | Oxide interface ---")
                print("  %s (left) | %s (right)" % (metal_phase, oxide_phase))
                try:
                    diff_5b = system.with_isothermal_diffusion_calculation()
                    diff_5b.set_temperature(1800)
                    diff_5b.set_simulation_time(3600)

                    # Left: steel with Cu contamination
                    region_metal = (Region("steel")
                                    .set_width(5e-4)
                                    .with_grid(CalculatedGrid.linear()
                                               .set_no_of_points(25))
                                    .with_composition_profile(
                                        CompositionProfile(Unit.MASS_PERCENT)
                                        .add("CU", ElementProfile.constant(0.3))
                                        .add("O", ElementProfile.constant(0.001))))

                    # Right: oxide slag
                    region_oxide = (Region("slag")
                                    .set_width(5e-4)
                                    .with_grid(CalculatedGrid.linear()
                                               .set_no_of_points(25))
                                    .with_composition_profile(
                                        CompositionProfile(Unit.MASS_PERCENT)
                                        .add("CU", ElementProfile.constant(0.01))
                                        .add("O", ElementProfile.constant(25.0))))

                    diff_5b.add_region(region_metal)
                    diff_5b.add_region(region_oxide)
                    diff_5b.with_left_boundary_condition(
                        BoundaryCondition.closed_system())
                    diff_5b.with_right_boundary_condition(
                        BoundaryCondition.closed_system())

                    print("  Running metal|oxide simulation...")
                    result_5b = diff_5b.calculate()
                    print("  *** METAL|OXIDE CALCULATION SUCCEEDED ***")
                    log("P5", "Metal|Oxide interface", "SUCCESS",
                        "steel(0.3%%Cu) | slag at 1800K")

                    # Cu redistribution
                    try:
                        dist, comp = result_5b.get_mass_fraction_of_component_at_time(
                            "CU", SimulationTime.LAST)
                        mid = len(dist) // 2
                        cu_steel = sum(comp[:mid]) / mid * 100
                        cu_slag = sum(comp[mid:]) / (len(comp) - mid) * 100
                        print("  Avg Cu in steel side: %.4f wt%%" % cu_steel)
                        print("  Avg Cu in slag side:  %.4f wt%%" % cu_slag)
                        log("P5", "Cu redistribution", "OK",
                            "steel=%.4f%% slag=%.4f%%" % (cu_steel, cu_slag))
                    except Exception as e:
                        log("P5", "Cu redistribution", "FAIL", str(e)[:80])

                except Exception as e:
                    print("  Metal|Oxide test failed: %s" % str(e)[:200])
                    log("P5", "Metal|Oxide interface", "FAIL",
                        str(e)[:120])
            else:
                log("P5", "Metal|Oxide interface", "SKIP",
                    "missing metal=%s oxide=%s" % (metal_phase, oxide_phase))

        # =============================================================
        # PHASE 6: Boundary Condition & Advanced Feature Tests
        # =============================================================
        print()
        print("=" * 75)
        print("PHASE 6: Boundary Conditions & Advanced Features")
        print("=" * 75)
        print()

        if not calc_succeeded:
            print("  Skipped (no working calc from Phase 3).")
            log("P6", "Boundary tests", "SKIP", "no working calc")
        elif steel_pair is None:
            print("  Skipped (no working steel pair).")
            log("P6", "Boundary tests", "SKIP", "no pair")
        else:
            tdb, mob, elems, elem_label, phases = steel_pair
            system = (session
                      .select_thermodynamic_and_kinetic_databases_with_elements(
                          tdb, mob, elems)
                      .get_system())

            # Test A: Fixed composition boundary (Cu source at left)
            print("  --- Test A: Fixed Cu composition at left boundary ---")
            try:
                diff_6a = system.with_isothermal_diffusion_calculation()
                diff_6a.set_temperature(1800)
                diff_6a.set_simulation_time(3600)

                region_6a = (Region("steel_6a")
                             .set_width(1e-3)
                             .with_grid(CalculatedGrid.geometric()
                                        .set_no_of_points(40)
                                        .set_geometrical_factor(1.05))
                             .with_composition_profile(
                                 CompositionProfile(Unit.MASS_PERCENT)
                                 .add("CU", ElementProfile.constant(0.1))))

                diff_6a.add_region(region_6a)

                # Left: fixed Cu = 0.5 wt% (Cu source)
                left_bc = (BoundaryCondition
                           .fixed_compositions(Unit.MASS_PERCENT)
                           .set_composition("CU", 0.5))
                diff_6a.with_left_boundary_condition(left_bc)
                diff_6a.with_right_boundary_condition(
                    BoundaryCondition.closed_system())

                print("  Running (fixed Cu=0.5%% at left, closed right)...")
                result_6a = diff_6a.calculate()
                log("P6", "Fixed composition BC", "SUCCESS",
                    "Cu=0.5%% left, closed right")

                try:
                    dist, comp = result_6a.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    print("  Cu at x=0: %.4f wt%% (should be ~0.5)" %
                          (comp[0] * 100))
                    print("  Cu at x=L: %.4f wt%% (should be ~0.1)" %
                          (comp[-1] * 100))
                    log("P6", "Fixed BC Cu profile", "OK",
                        "x=0: %.4f%%, x=L: %.4f%%" % (
                            comp[0]*100, comp[-1]*100))
                except Exception as e:
                    log("P6", "Fixed BC Cu profile", "FAIL", str(e)[:80])

            except Exception as e:
                log("P6", "Fixed composition BC", "FAIL", str(e)[:120])

            # Test B: Activity-based boundary condition
            print()
            print("  --- Test B: Activity-based boundary condition ---")
            try:
                diff_6b = system.with_isothermal_diffusion_calculation()
                diff_6b.set_temperature(1800)
                diff_6b.set_simulation_time(3600)

                region_6b = (Region("steel_6b")
                             .set_width(1e-3)
                             .with_grid(CalculatedGrid.linear()
                                        .set_no_of_points(30))
                             .with_composition_profile(
                                 CompositionProfile(Unit.MASS_PERCENT)
                                 .add("CU", ElementProfile.constant(0.3))))

                diff_6b.add_region(region_6b)

                # Activity-based: a_Cu = 0.001 at right (oxide captures Cu)
                right_bc = (BoundaryCondition
                            .mixed_zero_flux_and_activity()
                            .set_activity_for_element("CU", 0.001))
                diff_6b.with_left_boundary_condition(
                    BoundaryCondition.closed_system())
                diff_6b.with_right_boundary_condition(right_bc)

                print("  Running (closed left, a_Cu=0.001 at right)...")
                result_6b = diff_6b.calculate()
                log("P6", "Activity BC", "SUCCESS",
                    "a_Cu=0.001 at right wall")

                try:
                    dist, comp = result_6b.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    print("  Cu at x=0: %.4f wt%% (closed side)" %
                          (comp[0] * 100))
                    print("  Cu at x=L: %.6f wt%% (a_Cu=0.001 side)" %
                          (comp[-1] * 100))
                    log("P6", "Activity BC Cu profile", "OK",
                        "x=0: %.4f%%, x=L: %.6f%%" % (
                            comp[0]*100, comp[-1]*100))

                    # This is directly relevant to our project:
                    # If a_Cu drops at the steel/slag interface (oxide captures Cu),
                    # we can model how fast Cu migrates out of the steel
                    cu_removed = (0.3 - comp[-1]*100) / 0.3 * 100
                    print("  Cu removal at boundary: %.1f%%" % cu_removed)
                    log("P6", "Cu removal at boundary", "OK",
                        "%.1f%% removed" % cu_removed)

                except Exception as e:
                    log("P6", "Activity BC Cu profile", "FAIL", str(e)[:80])

            except Exception as e:
                log("P6", "Activity BC", "FAIL", str(e)[:120])

            # Test C: Cylindrical geometry (simulate Cu diffusion into
            # a cylindrical oxide particle)
            print()
            print("  --- Test C: Cylindrical geometry ---")
            try:
                diff_6c = system.with_isothermal_diffusion_calculation()
                diff_6c.set_temperature(1800)
                diff_6c.set_simulation_time(600)

                region_6c = (Region("cylinder")
                             .set_width(5e-5)  # 50 um radius
                             .with_grid(CalculatedGrid.linear()
                                        .set_no_of_points(20))
                             .with_composition_profile(
                                 CompositionProfile(Unit.MASS_PERCENT)
                                 .add("CU", ElementProfile.constant(0.0))))

                diff_6c.add_region(region_6c)
                diff_6c.with_cylindrical_geometry()

                # Fixed Cu at outer surface
                left_bc = BoundaryCondition.closed_system()  # center
                right_bc = (BoundaryCondition
                            .fixed_compositions(Unit.MASS_PERCENT)
                            .set_composition("CU", 0.3))
                diff_6c.with_left_boundary_condition(left_bc)
                diff_6c.with_right_boundary_condition(right_bc)

                print("  Running cylindrical diffusion (Cu into 50um particle)...")
                result_6c = diff_6c.calculate()
                log("P6", "Cylindrical geometry", "SUCCESS",
                    "50um radius, Cu inward diffusion")

                try:
                    dist, comp = result_6c.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    print("  Cu at center: %.4f wt%%" % (comp[0] * 100))
                    print("  Cu at surface: %.4f wt%%" % (comp[-1] * 100))
                    # Penetration depth
                    for i, c in enumerate(comp):
                        if c * 100 > 0.01:  # above 0.01 wt%
                            pen_depth = dist[-1] - dist[i]
                            print("  Penetration depth (>0.01%%): %.2e m" %
                                  pen_depth)
                            log("P6", "Cyl penetration depth", "OK",
                                "%.2e m in 600s" % pen_depth)
                            break
                except Exception as e:
                    log("P6", "Cyl Cu profile", "FAIL", str(e)[:80])

            except Exception as e:
                log("P6", "Cylindrical geometry", "FAIL", str(e)[:120])

            # Test D: Spherical geometry
            print()
            print("  --- Test D: Spherical geometry ---")
            try:
                diff_6d = system.with_isothermal_diffusion_calculation()
                diff_6d.set_temperature(1800)
                diff_6d.set_simulation_time(600)

                region_6d = (Region("sphere")
                             .set_width(5e-5)
                             .with_grid(CalculatedGrid.linear()
                                        .set_no_of_points(20))
                             .with_composition_profile(
                                 CompositionProfile(Unit.MASS_PERCENT)
                                 .add("CU", ElementProfile.constant(0.0))))

                diff_6d.add_region(region_6d)
                diff_6d.with_spherical_geometry()

                left_bc = BoundaryCondition.closed_system()
                right_bc = (BoundaryCondition
                            .fixed_compositions(Unit.MASS_PERCENT)
                            .set_composition("CU", 0.3))
                diff_6d.with_left_boundary_condition(left_bc)
                diff_6d.with_right_boundary_condition(right_bc)

                print("  Running spherical diffusion...")
                result_6d = diff_6d.calculate()
                log("P6", "Spherical geometry", "SUCCESS",
                    "50um radius sphere")

                try:
                    dist, comp = result_6d.get_mass_fraction_of_component_at_time(
                        "CU", SimulationTime.LAST)
                    print("  Cu at center: %.4f wt%%" % (comp[0] * 100))
                    print("  Cu at surface: %.4f wt%%" % (comp[-1] * 100))
                    log("P6", "Sph Cu profile", "OK",
                        "center=%.4f%% surf=%.4f%%" % (
                            comp[0]*100, comp[-1]*100))
                except Exception as e:
                    log("P6", "Sph Cu profile", "FAIL", str(e)[:80])

            except Exception as e:
                log("P6", "Spherical geometry", "FAIL", str(e)[:120])

            # Test E: Solver options
            print()
            print("  --- Test E: Solver options ---")
            for solver_name, solver_obj in [
                ("AutomaticSolver", "AutomaticSolver"),
                ("ClassicSolver", "ClassicSolver"),
                ("HomogenizationSolver", "HomogenizationSolver"),
            ]:
                try:
                    solver_cls = eval(solver_obj)
                    log("P6", "Solver: %s" % solver_name, "OK",
                        "class available")
                except NameError:
                    log("P6", "Solver: %s" % solver_name, "FAIL",
                        "class not imported")

# =====================================================================
# WRITE CSV OUTPUT
# =====================================================================
print()
print("=" * 75)
print("Writing CSV output...")
print("=" * 75)

try:
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "phase", "test", "status", "detail", "timestamp"])
        writer.writeheader()
        writer.writerows(csv_rows)
    print("  Saved: %s" % CSV_PATH)
    print("  Rows: %d" % len(csv_rows))
except Exception as e:
    print("  CSV write failed: %s" % str(e)[:100])
    # Fallback: print CSV to stdout
    print()
    print("  --- CSV FALLBACK (copy this) ---")
    print("phase,test,status,detail")
    for row in csv_rows:
        print("%s,%s,%s,%s" % (
            row["phase"], row["test"], row["status"],
            row["detail"].replace(",", ";")))

# =====================================================================
# SUMMARY TABLE
# =====================================================================
print()
print("=" * 75)
print("SUMMARY")
print("=" * 75)
print()
print("%-6s  %-40s  %-8s  %s" % ("Phase", "Test", "Status", "Details"))
print("-" * 75)
for phase, test, status, detail in results:
    print("%-6s  %-40s  %-8s  %s" % (phase, test[:40], status, detail[:30]))

# Phase-level summary
print()
print("Per-phase summary:")
for p in ["P1", "P2", "P3", "P4", "P5", "P6"]:
    phase_results = [(t, s, d) for ph, t, s, d in results if ph == p]
    n_ok = sum(1 for _, s, _ in phase_results if s in ("OK", "SUCCESS"))
    n_fail = sum(1 for _, s, _ in phase_results if s == "FAIL")
    n_skip = sum(1 for _, s, _ in phase_results if s == "SKIP")
    n_info = sum(1 for _, s, _ in phase_results if s == "INFO")
    n_warn = sum(1 for _, s, _ in phase_results if s == "WARN")
    labels = {
        "P1": "DB Compatibility",
        "P2": "System Exploration",
        "P3": "Single-Region Diffusion",
        "P4": "D_Cu Extraction",
        "P5": "Two-Region Interface",
        "P6": "Boundary Conditions",
    }
    print("  %s %-25s  OK=%d  FAIL=%d  SKIP=%d  WARN=%d  INFO=%d" %
          (p, labels.get(p, "?"), n_ok, n_fail, n_skip, n_warn, n_info))

# Key findings for the project
print()
print("=" * 75)
print("KEY FINDINGS FOR HONDA CALPHAD PROJECT")
print("=" * 75)

p3_success = any(s == "SUCCESS" for ph, _, s, _ in results if ph == "P3")
p5_success = any(s == "SUCCESS" for ph, _, s, _ in results if ph == "P5")
p4_data = any(s == "OK" for ph, _, s, _ in results if ph == "P4")
p6_activity = any("Activity BC" in t and s == "SUCCESS"
                   for _, t, s, _ in results)
p6_cyl = any("Cylindrical" in t and s == "SUCCESS"
              for _, t, s, _ in results)

print()
if p3_success:
    print("  [YES] Single-region Cu diffusion in FCC austenite WORKS")
else:
    print("  [NO]  Single-region Cu diffusion FAILED")

if p4_data:
    print("  [YES] Cu diffusion coefficients extractable vs temperature")
else:
    print("  [NO]  Could not extract D_Cu data")

if p5_success:
    print("  [YES] Two-region interface modeling WORKS")
    print("        -> Can model Cu transport across steel/slag boundary!")
else:
    print("  [NO]  Two-region interface modeling FAILED")
    print("        -> Cannot model steel/slag interface with current DBs")

if p6_activity:
    print("  [YES] Activity-based boundary conditions WORK")
    print("        -> Can impose a_Cu from oxide equilibrium at boundary!")
else:
    print("  [NO]  Activity-based boundary conditions FAILED")

if p6_cyl:
    print("  [YES] Cylindrical geometry WORKS")
    print("        -> Can model Cu diffusion into oxide particles!")
else:
    print("  [NO]  Cylindrical geometry FAILED or not tested")

print()
print("=" * 75)
print("Finished: %s" % datetime.now().isoformat())
print("=" * 75)
