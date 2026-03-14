#!/usr/bin/env python3
"""
Mass Balance Calculator for Cu Removal Experiments.

Given steel mass, initial/target Cu concentration, and oxide choice,
calculates:
  - Minimum oxide mass needed (stoichiometric, from ternary reaction)
  - Recommended oxide mass (with excess factor for kinetics)
  - Number of particles at various sizes
  - Total surface area
  - Estimated contact time (from D_Cu in liquid Fe)

This is the experiment design tool for Fontana Lab trials.

Usage:
  python3 mass_balance_calculator.py

No VM or TC-Python required — runs locally with standard Python.

Honda CALPHAD Project - MSE 4381 Capstone
"""

import math

# ===========================================================================
# OXIDE DATABASE (from screening results)
# ===========================================================================

# Ternary reaction data: Cu + MOx + O2 → CuMOy
# dG values at 1527°C (1800K) in kJ/mol from ternary_screening_results.csv
# Molar masses in g/mol, densities in kg/m³

OXIDES = {
    "Fe2O3": {
        "formula": "Fe₂O₃",
        "product": "CuFe₂O₄",
        "dG_1800K_kJ": -111.9,
        "MW_oxide": 159.69,    # g/mol Fe2O3
        "MW_product": 239.24,  # g/mol CuFe2O4
        "rho": 5240,           # kg/m³
        "mp_C": 1565,          # melting point °C
        "cu_per_mol": 1,       # mol Cu captured per mol oxide
        "notes": "Top candidate. Spinel product persists to 1700K.",
    },
    "V2O5": {
        "formula": "V₂O₅",
        "product": "Cu₃V₂O₈",
        "dG_1800K_kJ": -109.2,
        "MW_oxide": 181.88,
        "MW_product": 372.53,
        "rho": 3357,
        "mp_C": 690,
        "cu_per_mol": 3,       # 3 Cu per mol V2O5
        "notes": "Strong thermodynamic driving force. Low melting point.",
    },
    "MnO": {
        "formula": "MnO",
        "product": "CuMn₂O₄",
        "dG_1800K_kJ": -63.5,
        "MW_oxide": 70.94,
        "MW_product": 237.43,
        "rho": 5430,
        "mp_C": 1945,
        "cu_per_mol": 0.5,     # 1 Cu per 2 MnO
        "notes": "Spinel product. High melting point, refractory.",
    },
    "SiO2": {
        "formula": "SiO₂",
        "product": "Cu₂SiO₄",
        "dG_1800K_kJ": -50.2,
        "MW_oxide": 60.08,
        "MW_product": 183.15,
        "rho": 2650,
        "mp_C": 1713,
        "cu_per_mol": 2,       # 2 Cu per mol SiO2
        "notes": "Cheap, abundant. Product melts into slag.",
    },
    "Al2O3": {
        "formula": "Al₂O₃",
        "product": "CuAl₂O₄",
        "dG_1800K_kJ": -35.7,
        "MW_oxide": 101.96,
        "MW_product": 181.50,
        "rho": 3950,
        "mp_C": 2072,
        "cu_per_mol": 1,
        "notes": "Tested last year. Spinel reaction confirmed by Zhang.",
    },
}

# Physical constants
MW_CU = 63.546  # g/mol Cu
D_CU_LIQUID = 9.63e-10  # m²/s at 1800K (from DICTRA Phase 4)

# ===========================================================================
# CALCULATOR
# ===========================================================================

def calculate(steel_mass_kg, cu_init_wt, cu_target_wt, oxide_name,
              excess_factor=3.0, particle_radius_um=100):
    """Calculate oxide requirements for a Cu removal experiment.

    Args:
        steel_mass_kg: Mass of steel melt (kg)
        cu_init_wt: Initial Cu concentration (wt%)
        cu_target_wt: Target Cu concentration (wt%)
        oxide_name: Key from OXIDES dict (e.g., "Fe2O3")
        excess_factor: Multiply stoichiometric amount by this (default 3x)
        particle_radius_um: Particle radius in micrometers

    Returns:
        dict with all calculated values
    """
    ox = OXIDES[oxide_name]

    # Cu to remove (grams)
    cu_init_g = steel_mass_kg * 1000 * cu_init_wt / 100
    cu_target_g = steel_mass_kg * 1000 * cu_target_wt / 100
    cu_remove_g = cu_init_g - cu_target_g
    cu_remove_mol = cu_remove_g / MW_CU

    # Stoichiometric oxide needed
    # cu_per_mol = mol Cu captured per mol oxide
    oxide_mol_needed = cu_remove_mol / ox["cu_per_mol"]
    oxide_mass_stoich_g = oxide_mol_needed * ox["MW_oxide"]
    oxide_mass_rec_g = oxide_mass_stoich_g * excess_factor

    # Particle calculations
    r_m = particle_radius_um * 1e-6
    v_particle = (4/3) * math.pi * r_m**3  # m³
    m_particle = ox["rho"] * v_particle * 1000  # grams
    n_particles = oxide_mass_rec_g / m_particle
    a_particle = 4 * math.pi * r_m**2  # m²
    total_area_m2 = n_particles * a_particle
    total_area_cm2 = total_area_m2 * 1e4

    # Diffusion time estimate
    # Time for Cu to diffuse one particle radius: t ~ r^2 / (2*D)
    t_diffusion_s = r_m**2 / (2 * D_CU_LIQUID)

    # Oxide mass as wt% of steel
    oxide_wt_pct = oxide_mass_rec_g / (steel_mass_kg * 1000) * 100

    return {
        "oxide_name": oxide_name,
        "oxide_formula": ox["formula"],
        "product": ox["product"],
        "dG_kJ": ox["dG_1800K_kJ"],
        "steel_mass_kg": steel_mass_kg,
        "cu_init_wt": cu_init_wt,
        "cu_target_wt": cu_target_wt,
        "cu_remove_g": cu_remove_g,
        "cu_remove_mol": cu_remove_mol,
        "oxide_stoich_g": oxide_mass_stoich_g,
        "oxide_recommended_g": oxide_mass_rec_g,
        "oxide_wt_pct": oxide_wt_pct,
        "excess_factor": excess_factor,
        "particle_radius_um": particle_radius_um,
        "n_particles": n_particles,
        "total_surface_area_cm2": total_area_cm2,
        "diffusion_time_s": t_diffusion_s,
        "notes": ox["notes"],
    }


def print_result(r):
    """Pretty-print a calculation result."""
    print()
    print("=" * 65)
    print("  EXPERIMENT DESIGN: %s (%s)" % (r["oxide_formula"],
                                             r["oxide_name"]))
    print("=" * 65)
    print()
    print("  Reaction:  Cu + %s → %s" % (r["oxide_formula"], r["product"]))
    print("  dG(1800K): %.1f kJ/mol" % r["dG_kJ"])
    print()
    print("  Steel:     %.2f kg at %.2f wt%% Cu → %.2f wt%% Cu" % (
        r["steel_mass_kg"], r["cu_init_wt"], r["cu_target_wt"]))
    print("  Cu to remove: %.2f g (%.4f mol)" % (
        r["cu_remove_g"], r["cu_remove_mol"]))
    print()
    print("  --- Oxide Requirements ---")
    print("  Stoichiometric: %.2f g %s" % (
        r["oxide_stoich_g"], r["oxide_formula"]))
    print("  Recommended:    %.2f g (%.0fx excess)" % (
        r["oxide_recommended_g"], r["excess_factor"]))
    print("  As wt%% of steel: %.2f%%" % r["oxide_wt_pct"])
    print()
    print("  --- Particle Properties (R=%d um) ---" % r["particle_radius_um"])
    print("  Number of particles: %.2e" % r["n_particles"])
    print("  Total surface area:  %.1f cm^2" % r["total_surface_area_cm2"])
    print()
    print("  --- Kinetics Estimate ---")
    print("  D_Cu in liquid Fe: %.2e m^2/s (DICTRA, 1800K)" % D_CU_LIQUID)
    print("  Diffusion time (r^2/2D): %.0f s (%.1f min)" % (
        r["diffusion_time_s"], r["diffusion_time_s"] / 60))
    print("  (Time for Cu to diffuse one particle radius)")
    print()
    print("  Note: %s" % r["notes"])
    print()


# ===========================================================================
# MAIN — Run default scenarios
# ===========================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("Cu REMOVAL MASS BALANCE CALCULATOR")
    print("Honda CALPHAD - MSE 4381 Capstone")
    print("=" * 65)

    # Default experiment: 0.5 kg steel, 0.3% Cu → 0.1% Cu
    STEEL_KG = 0.5
    CU_INIT = 0.30
    CU_TARGET = 0.10

    print()
    print("Default scenario: %.1f kg steel, %.2f%% → %.2f%% Cu" % (
        STEEL_KG, CU_INIT, CU_TARGET))
    print()

    # Calculate for all oxides
    print("=" * 65)
    print("COMPARISON TABLE — All Oxides")
    print("=" * 65)
    print()
    print("%-8s  %-12s  %-10s  %-10s  %-10s  %-8s" % (
        "Oxide", "Product", "dG(kJ)", "Stoich(g)", "Rec(g)", "wt%"))
    print("-" * 65)

    for name in ["Fe2O3", "V2O5", "MnO", "SiO2", "Al2O3"]:
        r = calculate(STEEL_KG, CU_INIT, CU_TARGET, name,
                      excess_factor=3.0, particle_radius_um=100)
        print("%-8s  %-12s  %-10.1f  %-10.2f  %-10.2f  %-8.2f" % (
            r["oxide_formula"], r["product"], r["dG_kJ"],
            r["oxide_stoich_g"], r["oxide_recommended_g"],
            r["oxide_wt_pct"]))

    # Detailed printouts for top 3
    print()
    print("=" * 65)
    print("DETAILED ANALYSIS — Top 3 Candidates")
    print("=" * 65)

    for name in ["Fe2O3", "V2O5", "MnO"]:
        r = calculate(STEEL_KG, CU_INIT, CU_TARGET, name,
                      excess_factor=3.0, particle_radius_um=100)
        print_result(r)

    # Particle size sweep for Fe2O3
    print()
    print("=" * 65)
    print("PARTICLE SIZE SWEEP — Fe2O3 (best candidate)")
    print("=" * 65)
    print()
    print("%-12s  %-15s  %-15s  %-12s" % (
        "Radius(um)", "N particles", "Area(cm2)", "t_diff(min)"))
    print("-" * 60)

    for radius in [10, 25, 50, 100, 250, 500]:
        r = calculate(STEEL_KG, CU_INIT, CU_TARGET, "Fe2O3",
                      excess_factor=3.0, particle_radius_um=radius)
        print("%-12d  %-15.2e  %-15.1f  %-12.1f" % (
            radius, r["n_particles"], r["total_surface_area_cm2"],
            r["diffusion_time_s"] / 60))

    print()
    print("Key: t_diff = r^2/(2*D_Cu) = time for Cu to diffuse one")
    print("     particle radius. Actual contact time should be >= t_diff")
    print("     for Cu depletion around each particle.")
    print()
    print("Recommendation: R=50-100 um gives good balance of")
    print("  surface area vs handling. t_diff ~ 1-5 min is feasible")
    print("  in Fontana Lab induction furnace (10-30 min hold).")
