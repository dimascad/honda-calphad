#!/usr/bin/env python3
"""
Cu Removal Rate Prediction via DICTRA Spherical Particle Model.

Models a spherical oxide particle immersed in steel (liquid or solid)
across a range of temperatures. The particle surface imposes a low Cu
concentration (0.01 wt%), creating a concentration gradient that draws
Cu out of the surrounding steel.

Sweeps:
  - Temperatures:  1673-1923 K (1400-1650 C) in 25 K steps
  - Particle radii: 25, 50, 100, 250, 500 um
  - Contact times: 60, 300, 600, 1800 s (1, 5, 10, 30 min)

For each (temp, radius, time) triplet, extracts:
  - Cu concentration profile vs distance from particle center
  - Total Cu mass captured (integrated over depletion shell)
  - Depletion shell thickness (distance where Cu < 90% of bulk)

Output CSVs:
  - cu_removal_rate_profiles.csv   (full radial profiles)
  - cu_removal_rate_summary.csv    (one row per temp x radius x time)

Temperature notes:
  - Above ~1811 K (1538 C, pure Fe melting): steel is LIQUID
  - Below ~1811 K: steel is FCC_A1 (solid). D_Cu drops ~1000x.
  - Script automatically selects LIQUID or FCC_A1 per temperature.
  - Below-liquidus runs show how much slower solid-state removal would be.

Run on OSU VM:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cu_removal_rate.py

Expected runtime: ~5-10 minutes (260 DICTRA calculations).

Honda CALPHAD Project - MSE 4381 Capstone
"""

from datetime import datetime
import csv
import math
import os
import sys
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "tcpython", "raw")
PROFILE_CSV = os.path.join(OUTPUT_DIR, "cu_removal_rate_profiles.csv")
SUMMARY_CSV = os.path.join(OUTPUT_DIR, "cu_removal_rate_summary.csv")

# ===========================================================================
# PARAMETERS
# ===========================================================================

# Temperature sweep (K)
# 1673 K (1400 C) to 1923 K (1650 C) in 25 K steps = 11 temperatures
# Covers: solid steel (~1673-1773 K) + liquid steel (~1811-1923 K)
# The solidus/liquidus for Fe-0.3%Cu is near 1808-1812 K.
TEMPS_K = list(range(1673, 1924, 25))
# [1673, 1698, 1723, 1748, 1773, 1798, 1823, 1848, 1873, 1898, 1923]

# Approximate Fe liquidus (K) — above this, use LIQUID phase
# Pure Fe: 1811 K. Fe-0.3%Cu shifts it down slightly.
# Using 1800 K as the crossover to be safe.
LIQUIDUS_K = 1800

# Initial Cu in steel (wt%)
CU_INIT_WT = 0.30  # 0.3% Cu — typical contaminated scrap

# Cu concentration at particle surface (wt%)
# The oxide maintains near-zero Cu at the steel/oxide interface.
# From TCOX14: a_Cu ~ 0.0006 at equilibrium in Cu-Fe-O at 1800K.
# With gamma_Cu ~ 8.5, this corresponds to X_Cu ~ 7e-5, or ~0.008 wt%.
# Using 0.01 wt% as a round conservative value.
#
# NOTE: Cannot use activity BC (mixed_zero_flux_and_activity) because
# the Fe-Cu liquid miscibility gap creates two solutions for a given
# a_Cu — DICTRA picks the Cu-rich root (~100% Cu) instead of the
# Fe-rich root (~0.01% Cu), driving Cu TO the surface instead of away.
# Fixed composition BC avoids this ambiguity entirely.
CU_SURFACE_WT = 0.01

# Particle radii to sweep (meters)
RADII_UM = [25, 50, 100, 250, 500]
RADII_M = [r * 1e-6 for r in RADII_UM]

# Contact times to sweep (seconds)
TIMES_S = [60, 300, 600, 1800]
TIMES_LABEL = ["1 min", "5 min", "10 min", "30 min"]

# Steel shell around particle — must be large enough that the
# outer boundary stays at bulk Cu concentration.
# Rule: shell >> sqrt(2 * D * t_max). D ~ 1e-9 (liquid), t_max = 1800 s
# => sqrt(2 * 1e-9 * 1800) ~ 1.9 mm. Use 5 mm for safety.
# For solid (D ~ 1e-12), depletion < 60 um so 5 mm is very safe.
SHELL_WIDTH_M = 5e-3  # 5 mm of steel around particle

# Grid points — finer near the particle surface where gradients are steep
N_GRID_POINTS = 60

# Databases — confirmed working from Phase 3-6
THERMO_DB = "TCFE13"
MOBILITY_DB = "MOBFE8"
ELEMENTS = ["FE", "CU"]

# Density of steel (kg/m^3) — approximate, used for mass integration
RHO_STEEL = 7000.0

# ===========================================================================

print("=" * 75)
print("Cu REMOVAL RATE PREDICTION - DICTRA Spherical Particle Model")
print("Honda CALPHAD - Cu Removal from Recycled Steel")
print("Started: %s" % datetime.now().isoformat())
print("=" * 75)
print()
print("Parameters:")
print("  Temperatures:   %d K to %d K (%d steps)" % (
    TEMPS_K[0], TEMPS_K[-1], len(TEMPS_K)))
print("  Liquidus:       ~%d K (LIQUID above, FCC_A1 below)" % LIQUIDUS_K)
print("  Initial Cu:     %.2f wt%%" % CU_INIT_WT)
print("  Cu at surface:  %.3f wt%% (fixed composition BC)" % CU_SURFACE_WT)
print("  Particle radii: %s um" % RADII_UM)
print("  Contact times:  %s s" % TIMES_S)
print("  Steel shell:    %.1f mm" % (SHELL_WIDTH_M * 1e3))
print("  Grid points:    %d" % N_GRID_POINTS)
print("  Databases:      %s + %s" % (THERMO_DB, MOBILITY_DB))
print("  Total calcs:    %d" % (len(TEMPS_K) * len(RADII_UM) * len(TIMES_S)))
print()

# ===========================================================================
# TC-PYTHON SETUP
# ===========================================================================

try:
    from tc_python import *
    print("tc_python imported successfully.")
except ImportError:
    print("ERROR: tc_python not available. Run on OSU VM.")
    sys.exit(1)

print("Initializing TCPython session...")
_tcp_ctx = TCPython()
session = _tcp_ctx.__enter__()
print("Session ready.")
print()

# ===========================================================================
# Set up the thermodynamic + kinetic system
# ===========================================================================

print("Loading databases: %s + %s with elements %s" % (
    THERMO_DB, MOBILITY_DB, ELEMENTS))
try:
    system = (session
              .select_thermodynamic_and_kinetic_databases_with_elements(
                  THERMO_DB, MOBILITY_DB, ELEMENTS)
              .get_system())
    print("System loaded successfully.")
except Exception as e:
    print("FATAL: Could not load system: %s" % e)
    traceback.print_exc()
    sys.exit(1)

# Determine available phases
try:
    phases = system.get_phases_in_system()
    print("  Phases in system: %s" % phases)
except Exception:
    phases = []

# Find LIQUID and FCC_A1 phase names
liquid_phase = None
fcc_phase = None
for p in phases:
    pu = p.upper()
    if "LIQUID" in pu and liquid_phase is None:
        liquid_phase = p
    if "FCC" in pu and "A1" in pu and fcc_phase is None:
        fcc_phase = p

print("  LIQUID phase: %s" % (liquid_phase or "NOT FOUND"))
print("  FCC_A1 phase: %s" % (fcc_phase or "NOT FOUND"))
print()

if liquid_phase is None and fcc_phase is None:
    print("FATAL: Neither LIQUID nor FCC_A1 found in system.")
    sys.exit(1)

# ===========================================================================
# MAIN SWEEP: temperature x radius x time
# ===========================================================================

summary_rows = []
profile_rows = []

n_total = len(TEMPS_K) * len(RADII_UM) * len(TIMES_S)
n_done = 0
n_fail = 0
n_liquid = 0
n_solid = 0

for temp_K in TEMPS_K:
    temp_C = temp_K - 273.15

    # Select diffusion phase based on temperature
    if temp_K >= LIQUIDUS_K and liquid_phase:
        diff_phase = liquid_phase
        phase_label = "LIQUID"
        n_liquid_this = 0
    elif fcc_phase:
        diff_phase = fcc_phase
        phase_label = "FCC_A1"
        n_solid_this = 0
    else:
        diff_phase = liquid_phase  # fallback
        phase_label = "LIQUID (fallback)"

    print("=" * 75)
    print("TEMPERATURE: %d K (%.0f C) -- phase: %s" % (
        temp_K, temp_C, phase_label))
    print("=" * 75)

    for ri, (r_um, r_m) in enumerate(zip(RADII_UM, RADII_M)):
        print()
        print("  Particle radius: %d um" % r_um)

        for ti, (t_s, t_label) in enumerate(zip(TIMES_S, TIMES_LABEL)):
            n_done += 1
            tag = "[%d/%d]" % (n_done, n_total)

            try:
                calc = system.with_isothermal_diffusion_calculation()
                calc.set_temperature(temp_K)
                calc.set_simulation_time(t_s)

                region = Region("steel_shell").set_width(SHELL_WIDTH_M)
                region.add_phase(diff_phase)
                region = (region
                          .with_grid(CalculatedGrid.linear()
                                     .set_no_of_points(N_GRID_POINTS))
                          .with_composition_profile(
                              CompositionProfile(Unit.MASS_PERCENT)
                              .add("CU", ElementProfile.constant(CU_INIT_WT))))

                calc.add_region(region)
                calc.with_spherical_geometry()

                left_bc = (BoundaryCondition
                           .fixed_compositions(Unit.MASS_PERCENT)
                           .set_composition("CU", CU_SURFACE_WT))
                calc.with_left_boundary_condition(left_bc)
                calc.with_right_boundary_condition(
                    BoundaryCondition.closed_system())

                result = calc.calculate()

                # Extract final Cu profile
                dist, comp = result.get_mass_fraction_of_component_at_time(
                    "CU", SimulationTime.LAST)

                cu_wt = [c * 100 for c in comp]
                dist_um = [d * 1e6 for d in dist]
                radial_um = [r_um + d for d in dist_um]

                # Store profile data
                for k in range(len(dist)):
                    profile_rows.append({
                        "temp_K": temp_K,
                        "radius_um": r_um,
                        "time_s": t_s,
                        "time_label": t_label,
                        "distance_from_surface_um": dist_um[k],
                        "radial_position_um": radial_um[k],
                        "cu_wt_pct": cu_wt[k],
                    })

                # Depletion depth (where Cu < 90% of bulk)
                threshold = CU_INIT_WT * 0.90
                depletion_um = 0.0
                for k in range(len(cu_wt)):
                    if cu_wt[k] >= threshold:
                        depletion_um = dist_um[k]
                        break
                else:
                    depletion_um = dist_um[-1]

                cu_surface = cu_wt[0]

                # Integrated Cu removal (trapezoidal, spherical coords)
                cu_captured_kg = 0.0
                for k in range(1, len(dist)):
                    r1 = r_m + dist[k-1]
                    r2 = r_m + dist[k]
                    r_mid = 0.5 * (r1 + r2)
                    dr = dist[k] - dist[k-1]
                    dc1 = CU_INIT_WT/100 - comp[k-1]
                    dc2 = CU_INIT_WT/100 - comp[k]
                    dc_mid = 0.5 * (dc1 + dc2)
                    dv = 4 * math.pi * r_mid**2 * dr
                    cu_captured_kg += dc_mid * RHO_STEEL * dv

                cu_captured_mg = cu_captured_kg * 1e6

                # Cu removal % relative to initial Cu in modeled shell
                shell_vol = (4/3) * math.pi * (
                    (r_m + SHELL_WIDTH_M)**3 - r_m**3)
                total_cu_mg = CU_INIT_WT/100 * RHO_STEEL * shell_vol * 1e6
                cu_removed_pct = cu_captured_mg / total_cu_mg * 100

                print("    %s R=%3d um, t=%4s: Cu_surf=%.4f%%, "
                      "depl=%.0f um, captured=%.4e mg  OK" % (
                          tag, r_um, t_label, cu_surface,
                          depletion_um, cu_captured_mg))

                if temp_K >= LIQUIDUS_K:
                    n_liquid += 1
                else:
                    n_solid += 1

                summary_rows.append({
                    "temp_K": temp_K,
                    "phase": phase_label,
                    "radius_um": r_um,
                    "time_s": t_s,
                    "time_label": t_label,
                    "cu_surface_wt_pct": cu_surface,
                    "cu_farfield_wt_pct": cu_wt[-1],
                    "depletion_depth_um": depletion_um,
                    "cu_captured_mg": cu_captured_mg,
                    "cu_removed_shell_pct": cu_removed_pct,
                })

            except Exception as e:
                n_fail += 1
                print("    %s R=%3d um, t=%4s: FAILED: %s" % (
                    tag, r_um, t_label, str(e)[:100]))
                traceback.print_exc()
                summary_rows.append({
                    "temp_K": temp_K,
                    "phase": phase_label,
                    "radius_um": r_um,
                    "time_s": t_s,
                    "time_label": t_label,
                    "cu_surface_wt_pct": -1,
                    "cu_farfield_wt_pct": -1,
                    "depletion_depth_um": -1,
                    "cu_captured_mg": -1,
                    "cu_removed_shell_pct": -1,
                })

# ===========================================================================
# WRITE CSVs
# ===========================================================================

print()
print("=" * 75)
print("WRITING OUTPUT")
print("=" * 75)
print()

try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
except Exception:
    pass

# Summary CSV
try:
    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "temp_K", "phase", "radius_um", "time_s", "time_label",
            "cu_surface_wt_pct", "cu_farfield_wt_pct",
            "depletion_depth_um", "cu_captured_mg", "cu_removed_shell_pct",
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print("Summary CSV: %s (%d rows)" % (SUMMARY_CSV, len(summary_rows)))
except Exception as e:
    print("Could not write summary CSV: %s" % e)
    print("--- SUMMARY CSV FALLBACK (copy this) ---")
    print("temp_K,phase,radius_um,time_s,time_label,cu_surface_wt_pct,"
          "cu_farfield_wt_pct,depletion_depth_um,cu_captured_mg,"
          "cu_removed_shell_pct")
    for row in summary_rows:
        print("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
            row["temp_K"], row["phase"],
            row["radius_um"], row["time_s"], row["time_label"],
            row["cu_surface_wt_pct"], row["cu_farfield_wt_pct"],
            row["depletion_depth_um"], row["cu_captured_mg"],
            row["cu_removed_shell_pct"]))

# Profile CSV
try:
    with open(PROFILE_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "temp_K", "radius_um", "time_s", "time_label",
            "distance_from_surface_um", "radial_position_um", "cu_wt_pct",
        ])
        writer.writeheader()
        writer.writerows(profile_rows)
    print("Profile CSV: %s (%d rows)" % (PROFILE_CSV, len(profile_rows)))
except Exception as e:
    print("Could not write profile CSV: %s" % e)

# ===========================================================================
# QUICK REFERENCE TABLE (1800 K only, for comparison with previous run)
# ===========================================================================

print()
print("=" * 75)
print("REFERENCE TABLE (T=1800 K, 50g Fe2O3 dose per kg steel)")
print("=" * 75)
print()

RHO_FE2O3 = 5240  # kg/m^3
OXIDE_DOSE_KG = 0.050
STEEL_MASS_KG = 1.0
TOTAL_CU_MG = CU_INIT_WT / 100 * STEEL_MASS_KG * 1e6

print("%-10s  %-8s  %-12s  %-12s  %-15s  %-15s" % (
    "Radius", "Time", "Cu@surface", "Depletion", "Cu/particle",
    "50g dose removal"))
print("%-10s  %-8s  %-12s  %-12s  %-15s  %-15s" % (
    "(um)", "(s)", "(wt%)", "(um)", "(mg)", "(% of total Cu)"))
print("-" * 80)

ref_rows = [r for r in summary_rows if r["temp_K"] == 1800]
for row in ref_rows:
    if row["cu_captured_mg"] <= 0:
        print("%-10d  %-8d  FAIL" % (row["radius_um"], row["time_s"]))
        continue

    r_m = row["radius_um"] * 1e-6
    v_particle = (4/3) * math.pi * r_m**3
    m_particle = RHO_FE2O3 * v_particle
    n_particles = OXIDE_DOSE_KG / m_particle
    total_mg = row["cu_captured_mg"] * n_particles
    pct = total_mg / TOTAL_CU_MG * 100

    print("%-10d  %-8d  %-12.4f  %-12.0f  %-15.4e  %-15.2f" % (
        row["radius_um"], row["time_s"],
        row["cu_surface_wt_pct"], row["depletion_depth_um"],
        row["cu_captured_mg"], pct))

if not ref_rows:
    print("  (No 1800 K data — check LIQUIDUS_K setting)")

# ===========================================================================
# TEMPERATURE TREND (R=100 um, t=1800 s — one line per temperature)
# ===========================================================================

print()
print("=" * 75)
print("TEMPERATURE EFFECT (R=100 um, t=30 min)")
print("=" * 75)
print()
print("%-8s  %-8s  %-12s  %-12s  %-15s" % (
    "T (K)", "Phase", "Cu@surface", "Depletion", "Cu/particle (mg)"))
print("-" * 60)

for row in summary_rows:
    if row["radius_um"] == 100 and row["time_s"] == 1800:
        if row["cu_captured_mg"] > 0:
            print("%-8d  %-8s  %-12.4f  %-12.0f  %-15.4e" % (
                row["temp_K"], row["phase"],
                row["cu_surface_wt_pct"], row["depletion_depth_um"],
                row["cu_captured_mg"]))
        else:
            print("%-8d  %-8s  FAIL" % (row["temp_K"], row["phase"]))

# ===========================================================================
# FINAL SUMMARY
# ===========================================================================

print()
print("=" * 75)
print("Completed: %d/%d calculations (%d failed)" % (
    n_done - n_fail, n_done, n_fail))
print("  LIQUID phase runs: %d" % n_liquid)
print("  FCC_A1 phase runs: %d" % n_solid)
print("Finished: %s" % datetime.now().isoformat())
print("=" * 75)
