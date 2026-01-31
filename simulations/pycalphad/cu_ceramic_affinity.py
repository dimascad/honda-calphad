"""
Cu-Ceramic Affinity Calculations for Honda CALPHAD Project
MSE 4381 - Senior Design

This script calculates the thermodynamic favorability of reactions between
copper and various ceramic oxides. The goal is to identify ceramics that
can extract Cu from molten steel.

Approach:
1. Basic thermochemistry using tabulated Gibbs energy of formation (ΔGf)
2. Calculate ΔG_rxn = ΣΔGf(products) - ΣΔGf(reactants)
3. Negative ΔG_rxn indicates thermodynamically favorable reaction

For more advanced CALPHAD calculations (phase diagrams, activity coefficients),
we'll need appropriate TDB database files.
"""

import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# Thermodynamic Data (Standard Gibbs Energy of Formation)
# Units: kJ/mol
# Reference: NIST-JANAF tables, Barin thermochemical data
# =============================================================================

# Temperature range for calculations (K)
T = np.linspace(1273, 1873, 100)  # 1000°C to 1600°C (steel melting range)

def gibbs_formation_cu2o(T_K):
    """Cu2O: 2Cu + 1/2 O2 -> Cu2O"""
    # Approximate: ΔGf ≈ -170 + 0.075*T kJ/mol
    return -170 + 0.075 * T_K

def gibbs_formation_cuo(T_K):
    """CuO: Cu + 1/2 O2 -> CuO"""
    # Approximate: ΔGf ≈ -155 + 0.085*T kJ/mol
    return -155 + 0.085 * T_K

def gibbs_formation_al2o3(T_K):
    """Al2O3: 2Al + 3/2 O2 -> Al2O3"""
    # Very stable oxide
    # Approximate: ΔGf ≈ -1676 + 0.32*T kJ/mol
    return -1676 + 0.32 * T_K

def gibbs_formation_mgo(T_K):
    """MgO: Mg + 1/2 O2 -> MgO"""
    # Approximate: ΔGf ≈ -601 + 0.11*T kJ/mol
    return -601 + 0.11 * T_K

def gibbs_formation_sio2(T_K):
    """SiO2: Si + O2 -> SiO2"""
    # Approximate: ΔGf ≈ -910 + 0.18*T kJ/mol
    return -910 + 0.18 * T_K

def gibbs_formation_tio2(T_K):
    """TiO2: Ti + O2 -> TiO2"""
    # Approximate: ΔGf ≈ -944 + 0.18*T kJ/mol
    return -944 + 0.18 * T_K

def gibbs_formation_feo(T_K):
    """FeO: Fe + 1/2 O2 -> FeO"""
    # Approximate: ΔGf ≈ -264 + 0.065*T kJ/mol
    return -264 + 0.065 * T_K

# =============================================================================
# Reaction Analysis: Can Cu reduce these oxides?
# =============================================================================
#
# For Cu to "react" with an oxide (MxOy), we consider the exchange reaction:
#   Cu + MxOy -> CuOz + M (or other products)
#
# Key insight from thermodynamics:
# - If Cu can reduce the oxide, it means Cu has higher oxygen affinity
# - Compare Ellingham diagram positions
# - Lower (more negative) ΔGf/mol O2 = more stable oxide
#
# Reality: Cu oxides are LESS stable than Al2O3, MgO, SiO2, TiO2
# So direct reduction won't work.
#
# The ACTUAL mechanism (from meeting notes) involves:
# - Cu dissolving into ceramic structure
# - Formation of Cu-containing spinels or solid solutions
# - Physical adsorption at high temperatures
# =============================================================================

def ellingham_comparison():
    """
    Compare oxide stability via Ellingham diagram approach.
    More negative ΔG per mole O2 = more stable oxide.
    """
    print("=" * 60)
    print("ELLINGHAM DIAGRAM ANALYSIS")
    print("Comparing oxide stability at steelmaking temperature (1600°C)")
    print("=" * 60)

    T_steel = 1873  # K (1600°C, typical steel melting)

    # Calculate ΔGf per mole O2 for comparison
    oxides = {
        'Cu2O': gibbs_formation_cu2o(T_steel) / 0.5,  # per mol O2
        'CuO': gibbs_formation_cuo(T_steel) / 0.5,
        'FeO': gibbs_formation_feo(T_steel) / 0.5,
        'Al2O3': gibbs_formation_al2o3(T_steel) / 1.5,
        'MgO': gibbs_formation_mgo(T_steel) / 0.5,
        'SiO2': gibbs_formation_sio2(T_steel) / 1.0,
        'TiO2': gibbs_formation_tio2(T_steel) / 1.0,
    }

    # Sort by stability (most negative first)
    sorted_oxides = sorted(oxides.items(), key=lambda x: x[1])

    print(f"\nAt T = {T_steel} K ({T_steel-273:.0f}°C):")
    print(f"{'Oxide':<10} {'ΔGf (kJ/mol O2)':<20} {'Stability Rank':<15}")
    print("-" * 45)

    for rank, (oxide, dG) in enumerate(sorted_oxides, 1):
        print(f"{oxide:<10} {dG:<20.1f} {rank:<15}")

    print("\n" + "=" * 60)
    print("INTERPRETATION:")
    print("- Cu oxides are the LEAST stable (highest ΔG)")
    print("- Cu CANNOT reduce Al2O3, MgO, SiO2, or TiO2 directly")
    print("- The Cu removal mechanism must be different:")
    print("  → Solid solution formation")
    print("  → Spinel formation (Cu-Al-O compounds)")
    print("  → Physical adsorption/absorption")
    print("  → Sulfide exchange (as shown in meeting: FeS + Cu -> Cu2S + Fe)")
    print("=" * 60)

    return sorted_oxides


def plot_ellingham():
    """Generate Ellingham diagram for relevant oxides."""
    T_range = np.linspace(800, 2000, 200)  # K

    fig, ax = plt.subplots(figsize=(10, 8))

    # Calculate ΔG per mol O2 for each oxide
    ax.plot(T_range - 273, gibbs_formation_cu2o(T_range) / 0.5,
            '-', color='#0077BB', linewidth=2, label='Cu₂O (2Cu + ½O₂ → Cu₂O)')
    ax.plot(T_range - 273, gibbs_formation_feo(T_range) / 0.5,
            '--', color='#EE7733', linewidth=2, label='FeO (2Fe + O₂ → 2FeO)')
    ax.plot(T_range - 273, gibbs_formation_al2o3(T_range) / 1.5,
            ':', color='#AA3377', linewidth=2, label='Al₂O₃ (4/3Al + O₂ → 2/3Al₂O₃)')
    ax.plot(T_range - 273, gibbs_formation_mgo(T_range) / 0.5,
            '-', color='#009988', linewidth=2, label='MgO (2Mg + O₂ → 2MgO)')
    ax.plot(T_range - 273, gibbs_formation_sio2(T_range) / 1.0,
            '--', color='#CC3311', linewidth=2, label='SiO₂ (Si + O₂ → SiO₂)')
    ax.plot(T_range - 273, gibbs_formation_tio2(T_range) / 1.0,
            ':', color='#0077BB', linewidth=2, alpha=0.7, label='TiO₂ (Ti + O₂ → TiO₂)')

    # Steel melting range
    ax.axvspan(1400, 1600, alpha=0.15, color='gray', label='Steel melting range')

    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('ΔG° (kJ/mol O₂)', fontsize=12)
    ax.set_title('Ellingham Diagram: Oxide Stability Comparison\nHonda CALPHAD Cu Removal Project', fontsize=14)
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(500, 1700)
    ax.set_ylim(-1400, 0)

    # Remove outer spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    return fig


def sulfide_reaction_example():
    """
    Example from meeting notes: FeS + Cu -> Cu2S + Fe
    This shows how sulfides can be used to remove Cu.
    """
    print("\n" + "=" * 60)
    print("SULFIDE EXCHANGE REACTION (from meeting notes)")
    print("=" * 60)

    # Approximate thermodynamic data for sulfides
    # ΔGf values at 1600°C (1873 K)
    T = 1873  # K

    # FeS: Fe + 1/2 S2 -> FeS
    # ΔGf ≈ -100 kJ/mol at 1873 K
    dGf_FeS = -100  # kJ/mol

    # Cu2S: 2Cu + 1/2 S2 -> Cu2S
    # ΔGf ≈ -120 kJ/mol at 1873 K (Cu2S is more stable)
    dGf_Cu2S = -120  # kJ/mol

    # Reaction: 2Cu + FeS -> Cu2S + Fe
    # ΔG_rxn = ΔGf(Cu2S) + ΔGf(Fe) - ΔGf(Cu) - ΔGf(FeS)
    #        = ΔGf(Cu2S) - ΔGf(FeS)  (elements have ΔGf = 0)
    dG_rxn = dGf_Cu2S - dGf_FeS

    print(f"\nReaction: 2Cu(dissolved) + FeS(s) → Cu₂S(s) + Fe")
    print(f"Temperature: {T} K ({T-273}°C)")
    print(f"\nΔGf(FeS)  ≈ {dGf_FeS} kJ/mol")
    print(f"ΔGf(Cu₂S) ≈ {dGf_Cu2S} kJ/mol")
    print(f"\nΔG_reaction = ΔGf(Cu₂S) - ΔGf(FeS)")
    print(f"            = {dGf_Cu2S} - ({dGf_FeS})")
    print(f"            = {dG_rxn} kJ/mol")
    print(f"\nResult: ΔG < 0, reaction is THERMODYNAMICALLY FAVORABLE")
    print("Cu₂S is more stable than FeS, so Cu displaces Fe from FeS")
    print("=" * 60)


def oxide_interaction_mechanisms():
    """
    Discuss the actual mechanisms for Cu-oxide interactions.
    """
    print("\n" + "=" * 60)
    print("Cu-CERAMIC INTERACTION MECHANISMS")
    print("(Why Al2O3 can still capture Cu despite thermodynamics)")
    print("=" * 60)

    mechanisms = """
    Since Cu CANNOT reduce stable oxides like Al2O3, MgO, SiO2, TiO2,
    the Cu removal mechanism involves different phenomena:

    1. SOLID SOLUTION FORMATION
       - Cu can dissolve into certain oxide lattices at high T
       - Example: Cu in Al2O3 (limited solubility)
       - Driven by entropy, not oxide reduction

    2. SPINEL FORMATION
       - CuAl2O4 (copper aluminate spinel)
       - Reaction: CuO + Al2O3 → CuAl2O4
       - Requires Cu oxidation first (from dissolved O in steel)

    3. SURFACE ADSORPTION
       - Physical/chemical adsorption at particle surfaces
       - High surface area particles are beneficial
       - Temperature and surface chemistry dependent

    4. WETTING AND PENETRATION
       - Molten Cu/Cu compounds wetting ceramic particles
       - Capillary action drawing Cu into porous ceramics
       - Important for high-surface-area additions

    5. OXYGEN POTENTIAL GRADIENTS
       - Local oxygen activity differences
       - Cu oxidation at steel/ceramic interface
       - Oxide stability depends on local pO2

    NEXT STEPS FOR CALPHAD SIMULATION:
    - Model Cu-Al-O ternary system
    - Calculate phase diagrams at steelmaking temperatures
    - Determine Cu solubility in Al2O3 vs temperature
    - Compare different ceramics (MgO, SiO2, TiO2, spinels)
    """
    print(mechanisms)
    print("=" * 60)


def main():
    """Run all analyses."""
    print("\n" + "=" * 70)
    print("  HONDA CALPHAD PROJECT: Cu-Ceramic Affinity Analysis")
    print("  MSE 4381 Senior Design - Initial Thermodynamic Screening")
    print("=" * 70)

    # 1. Ellingham diagram analysis
    ellingham_comparison()

    # 2. Sulfide example from meeting
    sulfide_reaction_example()

    # 3. Actual mechanisms
    oxide_interaction_mechanisms()

    # 4. Generate plot
    print("\nGenerating Ellingham diagram plot...")
    fig = plot_ellingham()

    output_dir = '/Users/anthonydimascio/School/Spring2026/MSE-4381-Capstone/honda-calphad/simulations/pycalphad'
    fig.savefig(f'{output_dir}/ellingham_diagram.png', dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {output_dir}/ellingham_diagram.png")

    # plt.show()  # Uncomment for interactive viewing
    plt.close()


if __name__ == '__main__':
    main()
