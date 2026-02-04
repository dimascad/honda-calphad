#!/usr/bin/env python3
"""
Pre-compute thermodynamic data for Ellingham diagram comparison.

This script computes:
1. Cu-O system from pyCALPHAD (NIMS/Schramm 2005 database)
2. Other oxides (Al2O3, MgO, SiO2, TiO2, FeO) from linearized approximations

KEY FIX: pyCALPHAD's GM is per mole of SITES (sublattice positions), not per formula unit!
- Cu2O with sublattice (Cu)2(O)1 has 3 sites → multiply GM by 3
- CuO with sublattice (Cu)1(O)1 has 2 sites → multiply GM by 2

Formation reaction for Cu2O:
    2Cu(s) + 1/2 O2(g) -> Cu2O(s)
    dGf = G(Cu2O) - 2*GHSERCU - GHSEROO

Output: ../data/pycalphad/cu_o_gibbs_energies.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path
from pycalphad import Database, calculate

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 500      # K
T_MAX = 1900     # K (extended for steelmaking temps)
N_POINTS = 100
PRESSURE = 101325  # Pa (1 atm)

# Sublattice site counts (from TDB phase definitions)
SITES_CU2O = 3  # (Cu)2(O)1 = 2 + 1 = 3 sites
SITES_CUO = 2   # (Cu)1(O)1 = 1 + 1 = 2 sites

# =============================================================================
# Paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "databases" / "cuo.tdb"
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "pycalphad"
OUTPUT_FILE = OUTPUT_DIR / "cu_o_gibbs_energies.csv"

# =============================================================================
# SGTE Reference Functions from TDB file
# =============================================================================
def GHSERCU(T):
    """
    Gibbs energy of Cu in FCC_A1 reference state (J/mol).
    From cuo.tdb: FUNCTION GHSERCU
    """
    T = np.asarray(T, dtype=float)
    return np.where(
        T < 1358,
        -7770.458 + 130.485235*T - 24.112392*T*np.log(T)
        - 0.00265684*T**2 + 1.29223e-7*T**3 + 52478/T,
        # Above melting point (1358 K)
        -13542.026 + 183.803828*T - 31.38*T*np.log(T) + 3.64167e29*np.power(T, -9.0)
    )


def GHSEROO(T):
    """
    Gibbs energy of 1/2 mol O2 gas (J per 1/2 mol O2).
    From cuo.tdb: FUNCTION GHSEROO
    This is the SGTE reference for O element (1/2_MOLE_O2(G)).
    """
    T = np.asarray(T, dtype=float)
    result = np.zeros_like(T, dtype=float)

    # 298.15 - 1000 K
    mask1 = T < 1000
    result[mask1] = (-3480.87 - 25.503038*T[mask1] - 11.136*T[mask1]*np.log(T[mask1])
                     - 0.005098888*T[mask1]**2 + 6.61846e-7*T[mask1]**3 - 38365/T[mask1])

    # 1000 - 3300 K
    mask2 = (T >= 1000) & (T < 3300)
    result[mask2] = (-6568.763 + 12.65988*T[mask2] - 16.8138*T[mask2]*np.log(T[mask2])
                     - 5.95798e-4*T[mask2]**2 + 6.781e-9*T[mask2]**3 + 262905/T[mask2])

    # 3300 - 6000 K
    mask3 = T >= 3300
    result[mask3] = (-13986.728 + 31.259625*T[mask3] - 18.9536*T[mask3]*np.log(T[mask3])
                     - 4.25243e-4*T[mask3]**2 + 1.0721e-8*T[mask3]**3 + 4383200/T[mask3])

    return result


# =============================================================================
# Linearized oxide data for comparison (from cu_ceramic_thermodynamics.py)
# Format: (A, B, O2_factor) where dGf = A + B*T (kJ/mol), normalized by O2_factor
# =============================================================================
COMPARISON_OXIDES = {
    'Al2O3': (-1676, 0.32, 1.5),   # 4/3 Al + O2 -> 2/3 Al2O3
    'MgO':   (-601, 0.11, 0.5),    # 2Mg + O2 -> 2MgO
    'SiO2':  (-910, 0.18, 1.0),    # Si + O2 -> SiO2
    'TiO2':  (-944, 0.18, 1.0),    # Ti + O2 -> TiO2
    'FeO':   (-264, 0.065, 0.5),   # 2Fe + O2 -> 2FeO
}


def calc_comparison_oxide_dG(name, T_K):
    """Calculate dGf per mole O2 for comparison oxides (linearized)."""
    A, B, O2_factor = COMPARISON_OXIDES[name]
    return (A + B * T_K) / O2_factor * 1000  # Convert kJ to J


# =============================================================================
# Main Calculation
# =============================================================================
def main():
    print(f"Loading database: {DB_PATH}")
    db = Database(DB_PATH)

    print(f"Database elements: {db.elements}")
    print(f"Database phases: {list(db.phases.keys())}")

    # Temperature range
    T_range = np.linspace(T_MIN, T_MAX, N_POINTS)
    print(f"\nCalculating for T = {T_MIN}-{T_MAX} K ({N_POINTS} points)")

    # =========================================================================
    # Calculate reference state energies from SGTE functions
    # =========================================================================
    print("  Calculating SGTE reference states...")
    G_cu_ref = GHSERCU(T_range)      # J/mol Cu
    G_O_ref = GHSEROO(T_range)       # J per 1/2 mol O2 (= J per mol O)

    # =========================================================================
    # Calculate compound Gibbs energies from pyCALPHAD
    # IMPORTANT: pyCALPHAD GM is per mole of SITES, not formula units!
    # =========================================================================
    print("  Calculating Cu2O (pyCALPHAD)...")
    result_cu2o = calculate(db, ['CU', 'O'], 'CU2O', T=T_range, P=PRESSURE)
    GM_cu2o_per_site = result_cu2o.GM.values.flatten()
    G_cu2o = GM_cu2o_per_site * SITES_CU2O  # Convert to per formula unit

    print("  Calculating CuO (pyCALPHAD)...")
    result_cuo = calculate(db, ['CU', 'O'], 'CUO', T=T_range, P=PRESSURE)
    GM_cuo_per_site = result_cuo.GM.values.flatten()
    G_cuo = GM_cuo_per_site * SITES_CUO  # Convert to per formula unit

    # =========================================================================
    # Calculate Gibbs energy of FORMATION
    # =========================================================================
    print("  Calculating formation energies...")

    # Cu2O: 2Cu + 1/2 O2 -> Cu2O
    # Reference = 2*GHSERCU + 1*GHSEROO (1 mol O in Cu2O)
    dG_cu2o_formation = G_cu2o - 2*G_cu_ref - 1*G_O_ref  # J/mol Cu2O

    # CuO: Cu + 1/2 O2 -> CuO
    # Reference = 1*GHSERCU + 1*GHSEROO (1 mol O in CuO)
    dG_cuo_formation = G_cuo - 1*G_cu_ref - 1*G_O_ref  # J/mol CuO

    # =========================================================================
    # Normalize for Ellingham diagram (per mol O2)
    # =========================================================================
    # Cu2O uses 1/2 mol O2 per formula unit → multiply by 2 for per mol O2
    dG_cu2o_per_O2 = 2 * dG_cu2o_formation  # J/mol O2

    # CuO uses 1/2 mol O2 per formula unit → multiply by 2 for per mol O2
    dG_cuo_per_O2 = 2 * dG_cuo_formation  # J/mol O2

    # =========================================================================
    # Calculate comparison oxides (linearized approximations)
    # =========================================================================
    print("  Calculating comparison oxides (linearized)...")
    comparison_data = {}
    for oxide in COMPARISON_OXIDES:
        comparison_data[f'dG_{oxide}_per_O2'] = calc_comparison_oxide_dG(oxide, T_range)

    # =========================================================================
    # Create DataFrame
    # =========================================================================
    df = pd.DataFrame({
        'T_K': T_range,
        'T_C': T_range - 273.15,
        'G_cu2o': G_cu2o,
        'G_cuo': G_cuo,
        'G_cu_ref': G_cu_ref,
        'G_O_ref': G_O_ref,
        'dG_cu2o_formation': dG_cu2o_formation,
        'dG_cuo_formation': dG_cuo_formation,
        'dG_cu2o_per_O2': dG_cu2o_per_O2,
        'dG_cuo_per_O2': dG_cuo_per_O2,
        **comparison_data
    })

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")

    # =========================================================================
    # Print summary
    # =========================================================================
    idx_1600C = np.abs(T_range - 1873).argmin()

    print("\n" + "="*70)
    print("SUMMARY - Ellingham Diagram Values at 1600C (1873 K)")
    print("="*70)
    print(f"{'Oxide':<10} {'dG (kJ/mol O2)':<18} {'Source':<25}")
    print("-"*70)
    print(f"{'Cu2O':<10} {dG_cu2o_per_O2[idx_1600C]/1000:>+8.0f}          {'pyCALPHAD (Schramm 2005)':<25}")
    print(f"{'CuO':<10} {dG_cuo_per_O2[idx_1600C]/1000:>+8.0f}          {'pyCALPHAD (Schramm 2005)':<25}")
    for oxide in COMPARISON_OXIDES:
        val = comparison_data[f'dG_{oxide}_per_O2'][idx_1600C]
        print(f"{oxide:<10} {val/1000:>+8.0f}          {'Linearized (NIST)':<25}")
    print("="*70)
    print("\nExpected ordering (most to least stable, more negative = more stable):")
    print("  MgO > Al2O3 > TiO2 > SiO2 > FeO >> Cu2O > CuO")
    print("\nNote: CuO decomposes above ~1000C, so dG approaches 0 at 1600C.")
    print("="*70)


if __name__ == "__main__":
    main()
