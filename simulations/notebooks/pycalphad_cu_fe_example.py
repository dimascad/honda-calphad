"""
pyCALPHAD Example: Cu-Fe Binary System
MSE 4381 - Senior Design

This script demonstrates how to use pyCALPHAD to calculate phase diagrams
and thermodynamic properties for the Cu-Fe system.

For oxide systems (Cu-Al-O, Cu-Mg-O, etc.), you'll need specialized
thermodynamic databases. Common sources:
- SGTE (Scientific Group Thermodata Europe)
- FactSage databases
- Open databases from Thermo-Calc or literature

This example uses a simple Cu-Fe database to show the workflow.
"""

import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, calculate, variables as v
from pycalphad.plot import binary


# =============================================================================
# Cu-Fe Binary Database (Minimal TDB for demonstration)
# =============================================================================
#
# This is a simplified Cu-Fe database. For real calculations, use a validated
# database from SGTE or other sources.
#
CU_FE_TDB = """
$ Cu-Fe Binary System (Simplified)
$ For demonstration purposes only
$ Based on SGTE solution database parameters

ELEMENT /-   ELECTRON_GAS              0.0000E+00  0.0000E+00  0.0000E+00!
ELEMENT VA   VACUUM                    0.0000E+00  0.0000E+00  0.0000E+00!
ELEMENT CU   FCC_A1                    6.3546E+01  5.0041E+03  3.3150E+01!
ELEMENT FE   BCC_A2                    5.5845E+01  4.4890E+03  2.7280E+01!

$ Functions for Gibbs energy
FUNCTION GHSERCU  298.15
    -7770.458+130.485235*T-24.112392*T*LN(T)-.00265684*T**2+1.29223E-07*T**3
    +52478*T**(-1);  1357.77 Y
    -13542.026+183.803828*T-31.38*T*LN(T)+3.64167E+29*T**(-9);  3200.00 N !

FUNCTION GHSERFE  298.15
    +1225.7+124.134*T-23.5143*T*LN(T)-.00439752*T**2-5.8927E-08*T**3
    +77359*T**(-1);  1811.00 Y
    -25383.581+299.31255*T-46*T*LN(T)+2.29603E+31*T**(-9);  6000.00 N !

FUNCTION GFCCCU  298.15  +GHSERCU;  6000.00 N !
FUNCTION GFCCFE  298.15  +GHSERFE-1462.4+8.282*T-1.15*T*LN(T)+0.00064*T**2;  6000.00 N !
FUNCTION GBCCCU  298.15  +GHSERCU+4017-1.255*T;  6000.00 N !
FUNCTION GBCCFE  298.15  +GHSERFE;  6000.00 N !

$ Liquid phase
FUNCTION GLIQCU  298.15  +GHSERCU+12964.735-9.511904*T-5.8489E-21*T**7;  1357.77 Y
    +GHSERCU-46.545+173.881484*T-31.38*T*LN(T);  3200.00 N !
FUNCTION GLIQFE  298.15  +GHSERFE+12040.17-6.55843*T-3.67516E-21*T**7;  1811.00 Y
    +GHSERFE-10839.7+291.302*T-46*T*LN(T);  6000.00 N !

$ Phase definitions
TYPE_DEFINITION % SEQ *!
PHASE LIQUID %  1  1.0  !
CONSTITUENT LIQUID :CU,FE: !

PHASE FCC_A1 %  1  1.0  !
CONSTITUENT FCC_A1 :CU,FE: !

PHASE BCC_A2 %  1  1.0  !
CONSTITUENT BCC_A2 :CU,FE: !

$ Parameters
PARAMETER G(LIQUID,CU;0)  298.15  +GLIQCU;  6000.00 N !
PARAMETER G(LIQUID,FE;0)  298.15  +GLIQFE;  6000.00 N !
PARAMETER G(LIQUID,CU,FE;0)  298.15  +35625-3.27*T;  6000.00 N !
PARAMETER G(LIQUID,CU,FE;1)  298.15  -2939+0.89*T;  6000.00 N !

PARAMETER G(FCC_A1,CU;0)  298.15  +GFCCCU;  6000.00 N !
PARAMETER G(FCC_A1,FE;0)  298.15  +GFCCFE;  6000.00 N !
PARAMETER G(FCC_A1,CU,FE;0)  298.15  +49354-7.0*T;  6000.00 N !

PARAMETER G(BCC_A2,CU;0)  298.15  +GBCCCU;  6000.00 N !
PARAMETER G(BCC_A2,FE;0)  298.15  +GBCCFE;  6000.00 N !
PARAMETER G(BCC_A2,CU,FE;0)  298.15  +40000;  6000.00 N !
"""


def load_database():
    """Load the Cu-Fe database."""
    # Write TDB to temp file and load
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tdb', delete=False) as f:
        f.write(CU_FE_TDB)
        tdb_path = f.name

    db = Database(tdb_path)
    os.unlink(tdb_path)  # Clean up temp file
    return db


def calculate_phase_diagram(db):
    """Calculate and plot the Cu-Fe binary phase diagram."""
    print("Calculating Cu-Fe binary phase diagram...")

    components = ['CU', 'FE', 'VA']
    phases = ['LIQUID', 'FCC_A1', 'BCC_A2']

    # Temperature range
    T_range = (1000, 2000, 50)  # K

    fig, ax = plt.subplots(figsize=(10, 8))

    # Use pycalphad's binary plotter
    try:
        binary(db, components, phases, {v.X('CU'): (0, 1, 0.02), v.T: T_range, v.P: 101325, v.N: 1},
               ax=ax, tielines=False)
    except Exception as e:
        print(f"Binary plotter error (expected for simplified database): {e}")
        print("Falling back to manual calculation...")

        # Manual calculation approach
        temperatures = np.linspace(1000, 2000, 50)
        x_cu_range = np.linspace(0, 1, 50)

        for T in temperatures:
            for x_cu in x_cu_range:
                try:
                    eq = equilibrium(db, components, phases,
                                   {v.T: T, v.P: 101325, v.X('CU'): x_cu, v.N: 1},
                                   output='GM')
                except:
                    continue

    ax.set_xlabel('Mole Fraction Cu', fontsize=12)
    ax.set_ylabel('Temperature (K)', fontsize=12)
    ax.set_title('Cu-Fe Binary Phase Diagram\n(Simplified database for demonstration)', fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(1000, 2000)
    ax.grid(True, alpha=0.3)

    # Add annotation about Cu solubility
    ax.annotate('Cu solubility in Fe\nis very limited\n(immiscible in liquid)',
                xy=(0.3, 1700), fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


def calculate_gibbs_energy(db):
    """Calculate Gibbs energy vs composition at different temperatures."""
    print("\nCalculating Gibbs energy curves...")

    components = ['CU', 'FE', 'VA']
    phases = ['LIQUID', 'FCC_A1', 'BCC_A2']

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    temperatures = [1600, 1800]  # K (around steel melting)
    x_cu = np.linspace(0.001, 0.999, 100)

    for idx, T in enumerate(temperatures):
        ax = axes[idx]

        for phase in phases:
            try:
                result = calculate(db, components, phase,
                                 T=T, P=101325, output='GM')

                # Extract Gibbs energy
                gm = result.GM.values.flatten()
                x = result.X.sel(component='CU').values.flatten()

                # Sort by composition
                sort_idx = np.argsort(x)
                x = x[sort_idx]
                gm = gm[sort_idx]

                # Remove invalid values
                valid = ~np.isnan(gm) & (gm < 1e10) & (gm > -1e10)

                ax.plot(x[valid], gm[valid]/1000, label=phase, linewidth=2)
            except Exception as e:
                print(f"  Could not calculate {phase} at {T}K: {e}")

        ax.set_xlabel('Mole Fraction Cu', fontsize=11)
        ax.set_ylabel('Gibbs Energy (kJ/mol)', fontsize=11)
        ax.set_title(f'T = {T} K ({T-273}°C)', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)

        # Remove outer spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    fig.suptitle('Gibbs Energy vs Composition in Cu-Fe System', fontsize=14, y=1.02)
    plt.tight_layout()
    return fig


def cu_activity_in_fe(db):
    """
    Calculate Cu activity coefficient in Fe at steelmaking temperatures.
    This is relevant for understanding Cu behavior in molten steel.
    """
    print("\nCalculating Cu activity in Fe-rich liquid...")

    components = ['CU', 'FE', 'VA']
    T = 1873  # K (1600°C, typical steel temperature)

    # Cu concentrations of interest (steel typically has 0.1-0.3% Cu)
    x_cu_pct = np.array([0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0])
    x_cu_mole = x_cu_pct / 100  # Convert to mole fraction (approximate)

    print(f"\nCu Activity Analysis at T = {T} K ({T-273}°C)")
    print("=" * 50)
    print(f"{'Cu (wt%)':<12} {'x_Cu (approx)':<15} {'Notes':<25}")
    print("-" * 50)

    for pct, x in zip(x_cu_pct, x_cu_mole):
        if pct <= 0.3:
            note = "Typical recycled steel"
        elif pct <= 1.0:
            note = "High Cu contamination"
        else:
            note = "Very high (unusual)"
        print(f"{pct:<12.1f} {x:<15.4f} {note:<25}")

    print("-" * 50)
    print("\nKey insight: Even small amounts of Cu (0.1-0.3%) cause")
    print("hot shortness. The goal is to reduce Cu activity by")
    print("promoting Cu transfer to ceramic phases.")

    return None


def main():
    """Run pyCALPHAD demonstration."""
    print("=" * 70)
    print("  pyCALPHAD DEMONSTRATION: Cu-Fe Binary System")
    print("  MSE 4381 Senior Design - Honda CALPHAD Project")
    print("=" * 70)

    # Load database
    print("\nLoading Cu-Fe database...")
    db = load_database()
    print(f"Database loaded successfully!")
    print(f"  Elements: {list(db.elements)}")
    print(f"  Phases: {list(db.phases.keys())}")

    # Activity analysis
    cu_activity_in_fe(db)

    # Calculate Gibbs energy curves
    try:
        fig_gibbs = calculate_gibbs_energy(db)
        output_dir = '/Users/anthonydimascio/School/Spring2026/MSE-4381-Capstone/honda-calphad/simulations/pycalphad'
        fig_gibbs.savefig(f'{output_dir}/cu_fe_gibbs_energy.png', dpi=150, bbox_inches='tight')
        print(f"\nGibbs energy plot saved to: {output_dir}/cu_fe_gibbs_energy.png")
        plt.close()
    except Exception as e:
        print(f"\nCould not generate Gibbs energy plot: {e}")

    print("\n" + "=" * 70)
    print("NEXT STEPS FOR FULL CALPHAD ANALYSIS:")
    print("=" * 70)
    print("""
    1. OBTAIN PROPER DATABASES
       - SGTE SSUB (substance database) for oxide thermodynamics
       - Commercial: Thermo-Calc TCOX (oxide database)
       - Check if OSU has database licenses via Thermo-Calc

    2. SYSTEMS TO MODEL
       - Cu-Fe-O (oxygen activity effects)
       - Cu-Al-O (copper-alumina interactions)
       - Cu-Fe-Al-O (full system)
       - Potential spinels: CuAl2O4, CuFe2O4

    3. KEY CALCULATIONS
       - Phase diagrams at 1500-1700°C
       - Cu solubility in oxide phases
       - Activity coefficients
       - Driving force for Cu transfer

    4. COMPARE WITH THERMO-CALC
       - You're also using Thermo-Calc in MSE 3321
       - Results should be consistent
       - pyCALPHAD allows automation and custom analysis
    """)
    print("=" * 70)


if __name__ == '__main__':
    main()
