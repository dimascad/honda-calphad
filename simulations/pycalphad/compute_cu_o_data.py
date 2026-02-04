#!/usr/bin/env python3
"""
Pre-compute Cu-O thermodynamic data using pyCALPHAD.

This script runs the actual pyCALPHAD calculations and saves results to CSV,
so that the visualization notebook can run on Molab (which lacks pyCALPHAD).

Run this locally ONCE whenever you change temperature range or need new data:
    python compute_cu_o_data.py

Output: ../data/pycalphad/cu_o_gibbs_energies.csv

Database: cuo.tdb (NIMS/Schramm 2005)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from pycalphad import Database, calculate

# =============================================================================
# Configuration
# =============================================================================
T_MIN = 500      # K
T_MAX = 1400     # K
N_POINTS = 100
PRESSURE = 101325  # Pa (1 atm)

# =============================================================================
# Paths
# =============================================================================
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "databases" / "cuo.tdb"
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "pycalphad"
OUTPUT_FILE = OUTPUT_DIR / "cu_o_gibbs_energies.csv"

# =============================================================================
# Main Calculation
# =============================================================================
def main():
    print(f"Loading database: {DB_PATH}")
    db = Database(DB_PATH)

    print(f"Database elements: {db.elements}")
    print(f"Database phases: {list(db.phases.keys())}")

    # Temperature range
    T_range = np.linspace(T_MIN, T_MAX, N_POINTS)  # K
    print(f"\nCalculating for T = {T_MIN}-{T_MAX} K ({N_POINTS} points)")

    # Calculate Gibbs energies for each phase
    print("  Calculating Cu2O...")
    result_cu2o = calculate(db, ['CU', 'O'], 'CU2O', T=T_range, P=PRESSURE)
    G_cu2o = result_cu2o.GM.values.flatten()  # J/mol

    print("  Calculating CuO...")
    result_cuo = calculate(db, ['CU', 'O'], 'CUO', T=T_range, P=PRESSURE)
    G_cuo = result_cuo.GM.values.flatten()  # J/mol

    print("  Calculating Cu (fcc)...")
    # Pure Cu reference state: use GHSERCU directly from the TDB file
    # GHSERCU = -7770.458 + 130.485235*T - 24.112392*T*LN(T) - 0.00265684*T^2 + 1.29223E-07*T^3 + 52478*T^(-1)
    # (valid 298.15 to 1358 K; above 1358K different expression but we'll stay below)
    G_cu = np.where(
        T_range < 1358,
        -7770.458 + 130.485235*T_range - 24.112392*T_range*np.log(T_range)
        - 0.00265684*T_range**2 + 1.29223e-7*T_range**3 + 52478/T_range,
        # High-T expression (above melting)
        -13542.026 + 183.803828*T_range - 31.38*T_range*np.log(T_range)
    )

    # Calculate Gibbs energy of formation
    # Note: These are simplified - see notebook for full explanation
    dG_cu2o_formation = G_cu2o - 2 * G_cu  # per mol Cu2O
    dG_cuo_formation = G_cuo - G_cu        # per mol CuO

    # Normalize for Ellingham diagram (per mol O2)
    # 2Cu + 0.5O2 -> Cu2O, so for 1 mol O2: multiply by 2
    dG_cu2o_per_O2 = 2 * dG_cu2o_formation
    dG_cuo_per_O2 = 2 * dG_cuo_formation

    # Create DataFrame
    df = pd.DataFrame({
        'T_K': T_range,
        'T_C': T_range - 273.15,
        'G_cu2o': G_cu2o,        # Absolute Gibbs energy (J/mol)
        'G_cuo': G_cuo,
        'G_cu': G_cu,
        'dG_cu2o_formation': dG_cu2o_formation,  # Formation energy (J/mol)
        'dG_cuo_formation': dG_cuo_formation,
        'dG_cu2o_per_O2': dG_cu2o_per_O2,        # For Ellingham (J/mol O2)
        'dG_cuo_per_O2': dG_cuo_per_O2
    })

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Temperature range: {T_MIN}-{T_MAX} K ({T_MIN-273.15:.0f}-{T_MAX-273.15:.0f} °C)")
    print(f"Data points: {N_POINTS}")
    print(f"\nAt T = 1000°C (1273 K):")
    idx_1000C = np.abs(T_range - 1273).argmin()
    print(f"  dG(4Cu + O2 -> 2Cu2O) = {dG_cu2o_per_O2[idx_1000C]/1000:.1f} kJ/mol O2")
    print(f"  dG(2Cu + O2 -> 2CuO)  = {dG_cuo_per_O2[idx_1000C]/1000:.1f} kJ/mol O2")
    print(f"\nDatabase: Schramm et al. (2005), J. Phase Equilib. Diff. 26:605")
    print("="*60)


if __name__ == "__main__":
    main()
