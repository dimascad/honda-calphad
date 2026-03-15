#!/usr/bin/env python3
"""
Cu Removal Rate Prediction via DICTRA Spherical Particle Model.

Models a spherical oxide particle immersed in liquid steel at 1800K.
The particle surface imposes a low Cu concentration (0.01 wt%, from
TCOX14 oxide equilibrium where a_Cu ~ 0.0006), creating a concentration
gradient that draws Cu out of the surrounding steel.

Sweeps:
  - Particle radii: 25, 50, 100, 250, 500 um
  - Contact times: 60, 300, 600, 1800 s (1, 5, 10, 30 min)

For each (radius, time) pair, extracts:
  - Cu concentration profile vs distance from particle center
  - Total Cu mass captured (integrated over depletion shell)
  - Depletion shell thickness (distance where Cu < 90% of bulk)

Output CSVs:
  - cu_removal_rate_profiles.csv   (full radial profiles)
  - cu_removal_rate_summary.csv    (one row per radius x time combo)

Run on OSU VM:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cu_removal_rate.py

Expected runtime: 15-25 minutes (25 DICTRA calculations).

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

# Temperature (K) — steelmaking temperature
T_K = 1800

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
# Rule: shell >> sqrt(2 * D * t_max). D ~ 1e-9, t_max = 1800 s
# => sqrt(2 * 1e-9 * 1800) ~ 1.9 mm. Use 5 mm for safety.
SHELL_WIDTH_M = 5e-3  # 5 mm of liquid steel around particle

# Grid points — finer near the particle surface where gradients are steep
N_GRID_POINTS = 60

# Databases — confirmed working from Phase 3-6
THERMO_DB = "TCFE13"
MOBILITY_DB = "MOBFE8"
ELEMENTS = ["FE", "CU"]

# Density of liquid steel at 1800K (kg/m^3)
RHO_STEEL = 7000.0

# ===========================================================================

print("=" * 75)
print("Cu REMOVAL RATE PREDICTION - DICTRA Spherical Particle Model")
print("Honda CALPHAD - Cu Removal from Recycled Steel")
print("Started: %s" % datetime.now().isoformat())
print("=" * 75)
print()
print("Parameters:")
print("  Temperature:    %d K (%.0f C)" % (T_K, T_K - 273.15))
print("  Initial Cu:     %.2f wt%%" % CU_INIT_WT)
print("  Cu at surface:   %.3f wt%% (fixed composition BC)" % CU_SURFACE_WT)
print("  Particle radii: %s um" % RADII_UM)
print("  Contact times:  %s s" % TIMES_S)
print("  Steel shell:    %.1f mm" % (SHELL_WIDTH_M * 1e3))
print("  Grid points:    %d" % N_GRID_POINTS)
print("  Databases:      %s + %s" % (THERMO_DB, MOBILITY_DB))
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
# MUST use context manager — TCPython().__enter__() returns the session
# object that has select_thermodynamic_and_kinetic_databases_with_elements.
# Raw TCPython() does NOT expose this method.
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

# Determine available phases — at 1800K, steel is LIQUID
try:
    phases = system.get_phases_in_system()
    print("  Phases in system: %s" % phases)
except Exception:
    phases = []

# At 1800K, steel is LIQUID — must use LIQUID phase for diffusion.
# FCC_A1 is only valid below the solidus (~1723K for Fe-Cu).
diff_phase = None
for p in phases:
    if "LIQUID" in p.upper():
        diff_phase = p
        break
if diff_phase is None:
    # Fallback to FCC if LIQUID not available (e.g., lower temperature)
    for p in phases:
        if "FCC" in p.upper() and "A1" in p.upper():
            diff_phase = p
            break
if diff_phase is None:
    diff_phase = "LIQUID"  # last resort default

print("  Diffusion phase: %s" % diff_phase)
print()

# ===========================================================================
# MAIN SWEEP: radius x time
# ===========================================================================

summary_rows = []   # (radius_um, time_s, time_label, cu_depleted_pct,
#                      depletion_depth_um, cu_captured_mg_per_particle)
profile_rows = []   # (radius_um, time_s, distance_um, cu_wt_pct)

n_total = len(RADII_UM) * len(TIMES_S)
n_done = 0
n_fail = 0

# Run one DICTRA calculation per (radius, time) pair.
# We always query SimulationTime.LAST (confirmed working in Phase 6).
# SimulationTime(specific_value) has NOT been tested, so we avoid it.
# At ~1s per calc for liquid-phase diffusion, 20 calcs ~ 20-60s total.

for ri, (r_um, r_m) in enumerate(zip(RADII_UM, RADII_M)):
    print("-" * 75)
    print("Particle radius: %d um (%.2e m)" % (r_um, r_m))
    print("-" * 75)

    for ti, (t_s, t_label) in enumerate(zip(TIMES_S, TIMES_LABEL)):
        n_done += 1
        print()
        print("  [%d/%d] R=%d um, t=%s (%d s)" % (
            n_done, n_total, r_um, t_label, t_s))

        # The region models the STEEL SHELL around the particle.
        # Left boundary = particle surface (activity BC, oxide captures Cu)
        # Right boundary = far field (closed, bulk steel)
        #
        # In DICTRA spherical geometry, the diffusion equation uses
        # 1/r^2 d/dr(r^2 dC/dr), which enhances flux convergence toward
        # the particle center — exactly the physics we want.

        try:
            calc = system.with_isothermal_diffusion_calculation()
            calc.set_temperature(T_K)
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

            # Left BC: particle surface — oxide maintains low Cu
            # Using fixed composition instead of activity BC to avoid
            # the Fe-Cu miscibility gap dual-root problem.
            left_bc = (BoundaryCondition
                       .fixed_compositions(Unit.MASS_PERCENT)
                       .set_composition("CU", CU_SURFACE_WT))
            calc.with_left_boundary_condition(left_bc)

            # Right BC: closed (far-field, no Cu flux out of the system)
            calc.with_right_boundary_condition(
                BoundaryCondition.closed_system())

            print("    Running DICTRA (Cu=%.3f wt%% at surface)..." %
                  CU_SURFACE_WT)
            result = calc.calculate()

            # Extract final Cu profile
            dist, comp = result.get_mass_fraction_of_component_at_time(
                "CU", SimulationTime.LAST)

            # Convert to wt% and um
            cu_wt = [c * 100 for c in comp]
            dist_um = [d * 1e6 for d in dist]

            # Actual radial position = r_particle + distance from surface
            radial_um = [r_um + d for d in dist_um]

            # Store profile data
            for k in range(len(dist)):
                profile_rows.append({
                    "radius_um": r_um,
                    "time_s": t_s,
                    "time_label": t_label,
                    "distance_from_surface_um": dist_um[k],
                    "radial_position_um": radial_um[k],
                    "cu_wt_pct": cu_wt[k],
                })

            # Analysis: depletion depth (where Cu < 90% of bulk)
            threshold = CU_INIT_WT * 0.90
            depletion_um = 0.0
            for k in range(len(cu_wt)):
                if cu_wt[k] >= threshold:
                    depletion_um = dist_um[k]
                    break
            else:
                depletion_um = dist_um[-1]  # entire shell depleted

            cu_surface = cu_wt[0]

            # Integrated Cu removal: mass captured by the particle
            # Integrate (C_init - C(r)) * 4*pi*r^2 * dr over the shell
            # Using trapezoidal rule in spherical coordinates
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

            # Cu removal % relative to initial Cu in the modeled shell
            shell_vol = (4/3) * math.pi * (
                (r_m + SHELL_WIDTH_M)**3 - r_m**3)
            total_cu_mg = CU_INIT_WT/100 * RHO_STEEL * shell_vol * 1e6
            cu_removed_pct = cu_captured_mg / total_cu_mg * 100

            print("    Cu at surface:     %.4f wt%% (was %.2f)" % (
                cu_surface, CU_INIT_WT))
            print("    Cu at far field:   %.4f wt%%" % cu_wt[-1])
            print("    Depletion depth:   %.0f um" % depletion_um)
            print("    Cu captured:       %.4e mg/particle" %
                  cu_captured_mg)

            summary_rows.append({
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
            print("    FAILED: %s" % str(e)[:120])
            traceback.print_exc()
            summary_rows.append({
                "radius_um": r_um,
                "time_s": t_s,
                "time_label": t_label,
                "cu_surface_wt_pct": -1,
                "cu_farfield_wt_pct": -1,
                "depletion_depth_um": -1,
                "cu_captured_mg": -1,
                "cu_removed_shell_pct": -1,
            })

    print()

# ===========================================================================
# WRITE CSVs
# ===========================================================================

print("=" * 75)
print("WRITING OUTPUT")
print("=" * 75)
print()

# Ensure output directory exists
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
except Exception:
    pass

# Summary CSV
try:
    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "radius_um", "time_s", "time_label",
            "cu_surface_wt_pct", "cu_farfield_wt_pct",
            "depletion_depth_um", "cu_captured_mg", "cu_removed_shell_pct",
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print("Summary CSV: %s (%d rows)" % (SUMMARY_CSV, len(summary_rows)))
except Exception as e:
    print("Could not write summary CSV: %s" % e)
    print("--- SUMMARY CSV FALLBACK (copy this) ---")
    print("radius_um,time_s,time_label,cu_surface_wt_pct,cu_farfield_wt_pct,"
          "depletion_depth_um,cu_captured_mg,cu_removed_shell_pct")
    for row in summary_rows:
        print("%s,%s,%s,%s,%s,%s,%s,%s" % (
            row["radius_um"], row["time_s"], row["time_label"],
            row["cu_surface_wt_pct"], row["cu_farfield_wt_pct"],
            row["depletion_depth_um"], row["cu_captured_mg"],
            row["cu_removed_shell_pct"]))

# Profile CSV
try:
    with open(PROFILE_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "radius_um", "time_s", "time_label",
            "distance_from_surface_um", "radial_position_um", "cu_wt_pct",
        ])
        writer.writeheader()
        writer.writerows(profile_rows)
    print("Profile CSV: %s (%d rows)" % (PROFILE_CSV, len(profile_rows)))
except Exception as e:
    print("Could not write profile CSV: %s" % e)
    # Profile is too large for fallback — skip

# ===========================================================================
# PRACTICAL SCALING ESTIMATES
# ===========================================================================

print()
print("=" * 75)
print("PRACTICAL SCALING ESTIMATES")
print("=" * 75)
print()

# For each radius, calculate how many particles per kg of oxide,
# then total Cu removal for a given oxide dose.

# Use Fe2O3 as the reference oxide (most promising candidate via CuFe2O4)
RHO_FE2O3 = 5240  # kg/m^3
MW_FE2O3 = 159.69  # g/mol

print("Reference oxide: Fe2O3 (rho=%.0f kg/m3)" % RHO_FE2O3)
print("Steel: 1 kg at %.2f wt%% Cu (%.0f mg Cu)" % (
    CU_INIT_WT, CU_INIT_WT * 10))  # 0.3 wt% of 1000g = 3000 mg
print("Oxide dose: 50 g Fe2O3 per kg steel (5 wt%%)")
print()

OXIDE_DOSE_KG = 0.050  # 50 g
STEEL_MASS_KG = 1.0
TOTAL_CU_MG = CU_INIT_WT / 100 * STEEL_MASS_KG * 1e6  # mg

for row in summary_rows:
    if row["cu_captured_mg"] <= 0:
        continue
    r_um = row["radius_um"]
    r_m = r_um * 1e-6
    t_s = row["time_s"]
    t_label = row["time_label"]
    cu_per_particle = row["cu_captured_mg"]

    # Number of particles in the dose
    v_particle = (4/3) * math.pi * r_m**3
    m_particle = RHO_FE2O3 * v_particle  # kg per particle
    n_particles = OXIDE_DOSE_KG / m_particle

    # Total Cu captured
    total_captured_mg = cu_per_particle * n_particles
    removal_pct = total_captured_mg / TOTAL_CU_MG * 100

    if t_s == TIMES_S[0] or t_s == TIMES_S[-1]:  # print 1st and last time
        print("  R=%3d um, t=%4s: %.4e mg/particle x %.2e particles "
              "= %.1f mg Cu (%.2f%% of %.0f mg)" % (
                  r_um, t_label, cu_per_particle, n_particles,
                  total_captured_mg, removal_pct, TOTAL_CU_MG))

print()
print("(Full results in summary CSV)")

# ===========================================================================
# SUMMARY TABLE
# ===========================================================================

print()
print("=" * 75)
print("SUMMARY TABLE")
print("=" * 75)
print()
print("%-10s  %-8s  %-12s  %-12s  %-15s  %-15s" % (
    "Radius", "Time", "Cu@surface", "Depletion", "Cu/particle",
    "50g dose removal"))
print("%-10s  %-8s  %-12s  %-12s  %-15s  %-15s" % (
    "(um)", "(s)", "(wt%)", "(um)", "(mg)", "(% of total Cu)"))
print("-" * 80)

for row in summary_rows:
    if row["cu_captured_mg"] <= 0:
        print("%-10d  %-8d  %-12s  %-12s  %-15s  %-15s" % (
            row["radius_um"], row["time_s"],
            "FAIL", "FAIL", "FAIL", "FAIL"))
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

print()
print("=" * 75)
print("Completed: %d/%d calculations (%d failed)" % (
    n_done - n_fail, n_done, n_fail))
print("Finished: %s" % datetime.now().isoformat())
print("=" * 75)
