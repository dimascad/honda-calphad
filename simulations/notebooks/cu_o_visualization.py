import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    from pathlib import Path
    return Path, mo, np, pd, plt


@app.cell
def _(mo):
    mo.md(r"""
    # Cu-O System: CALPHAD Analysis
    ## Honda CALPHAD Project | MSE 4381 Senior Design

    **Pre-computed pyCALPHAD data — no local dependencies required.**

    This notebook visualizes Gibbs free energies of copper oxides (Cu₂O, CuO)
    calculated using pyCALPHAD with the Schramm et al. (2005) database.

    ---

    ## What is CALPHAD?

    **CALPHAD** = **CAL**culation of **PHA**se **D**iagrams

    The CALPHAD method:
    1. Models Gibbs energy of each phase as a function of T, P, and composition
    2. Uses assessed parameters fit to experimental data
    3. Minimizes total Gibbs energy to find equilibrium phases

    The key equation for Gibbs energy of a pure substance:

    $$G(T) = a + bT + cT\ln(T) + dT^2 + eT^3 + fT^{-1} + ...$$

    The coefficients (a, b, c, d, e, f, ...) are stored in **TDB files** (Thermodynamic DataBase format).
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## The Database: Cu-O System (NIMS/Schramm 2005)

    This data was computed using pyCALPHAD with the assessment from:

    > **L. Schramm, G. Behr, W. Löser, and K. Wetzig**
    > "Thermodynamic Reassessment of the Cu-O Phase Diagram"
    > *J. Phase Equilibria and Diffusion*, Vol. 26, No. 6, pp. 605-612 (2005)

    **Phases in this database:**
    | Phase | Formula | Description |
    |-------|---------|-------------|
    | CU2O | Cu₂O | Cuprite (copper(I) oxide) |
    | CUO | CuO | Tenorite (copper(II) oxide) |
    | FCC_A1 | Cu(s) | Solid copper |
    | IONIC_LIQ | Cu⁺/Cu²⁺/O²⁻ | Liquid phase |
    | GAS | O₂ | Oxygen gas |
    """)
    return


@app.cell
def _(Path, mo, pd):
    # Load pre-computed data
    # Try multiple possible locations for the CSV
    possible_paths = [
        Path(__file__).parent.parent.parent / "data" / "pycalphad" / "cu_o_gibbs_energies.csv",
        Path(__file__).parent / "data" / "cu_o_gibbs_energies.csv",
        Path("data/pycalphad/cu_o_gibbs_energies.csv"),
    ]

    df = None
    data_path = None
    for p in possible_paths:
        if p.exists():
            df = pd.read_csv(p)
            data_path = p
            break

    # Fallback: embed sampled data directly (computed on 2026-02-03)
    # Includes Cu2O, CuO from pyCALPHAD and comparison oxides from linearized NIST data
    if df is None:
        import io
        embedded_csv = """T_K,T_C,G_cu2o,G_cuo,G_cu_ref,G_O_ref,dG_cu2o_formation,dG_cuo_formation,dG_cu2o_per_O2,dG_cuo_per_O2,dG_Al2O3_per_O2,dG_MgO_per_O2,dG_SiO2_per_O2,dG_TiO2_per_O2,dG_FeO_per_O2
500.0,226.85,-220333.47,-180107.23,-17995.47,-52104.05,-132238.47,-110007.71,-264476.94,-220015.42,-1010666.67,-1092000.0,-820000.0,-854000.0,-463000.0
600.0,326.85,-235481.21,-187899.55,-22708.77,-63090.27,-126973.4,-102100.51,-253946.8,-204201.02,-978000.0,-1068000.0,-802000.0,-836000.0,-449000.0
700.0,426.85,-250726.49,-195758.03,-27553.85,-73898.25,-121820.54,-94306.03,-243641.08,-188612.06,-945333.33,-1044000.0,-784000.0,-818000.0,-435000.0
800.0,526.85,-266076.49,-203706.24,-32526.53,-84498.96,-116524.47,-86680.75,-233048.94,-173361.5,-912666.67,-1020000.0,-766000.0,-800000.0,-421000.0
900.0,626.85,-281535.87,-211760.29,-37620.1,-94882.77,-111113.0,-79257.42,-222226.0,-158514.84,-880000.0,-996000.0,-748000.0,-782000.0,-407000.0
1000.0,726.85,-297106.73,-219929.09,-42827.69,-105049.86,-105601.49,-72051.54,-211202.98,-144103.08,-847333.33,-972000.0,-730000.0,-764000.0,-393000.0
1100.0,826.85,-312789.15,-228218.3,-48142.96,-115007.29,-99998.94,-65063.05,-199997.88,-130126.1,-814666.67,-948000.0,-712000.0,-746000.0,-379000.0
1200.0,926.85,-328581.71,-236630.57,-53559.87,-124765.65,-94296.32,-58305.05,-188592.64,-116610.1,-782000.0,-924000.0,-694000.0,-728000.0,-365000.0
1300.0,1026.85,-344482.42,-245167.89,-59073.15,-134336.29,-88536.69,-51758.45,-177073.38,-103516.9,-749333.33,-900000.0,-676000.0,-710000.0,-351000.0
1400.0,1126.85,-360489.13,-253830.59,-64678.02,-143730.32,-82753.09,-45422.25,-165506.18,-90844.5,-716666.67,-876000.0,-658000.0,-692000.0,-337000.0
1500.0,1226.85,-376599.56,-262618.66,-70370.29,-152958.48,-76970.5,-39289.89,-153941.0,-78579.78,-684000.0,-852000.0,-640000.0,-674000.0,-323000.0
1600.0,1326.85,-392811.39,-271531.83,-76145.95,-162031.17,-71217.22,-33354.71,-142434.44,-66709.42,-651333.33,-828000.0,-622000.0,-656000.0,-309000.0
1700.0,1426.85,-409122.33,-280569.73,-82001.29,-170958.46,-65530.29,-27609.98,-131060.58,-55219.96,-618666.67,-804000.0,-604000.0,-638000.0,-295000.0
1800.0,1526.85,-425530.15,-289731.96,-87932.83,-179750.21,-59926.28,-22048.92,-119852.56,-44097.84,-586000.0,-780000.0,-586000.0,-620000.0,-281000.0
1900.0,1626.85,-442032.73,-299017.99,-93937.31,-188415.99,-54430.44,-16664.69,-108860.88,-33329.38,-553333.33,-756000.0,-568000.0,-602000.0,-267000.0"""
        df = pd.read_csv(io.StringIO(embedded_csv))
        data_path = "embedded (pre-computed 2026-02-03)"

    mo.md(f"""
    ---

    ## Data Loaded

    **Source:** `{data_path}`

    **Cu-O data:** pyCALPHAD with Schramm et al. (2005) database
    **Comparison oxides:** Linearized approximations from NIST-JANAF tables

    **Columns available:**
    {list(df.columns)}

    **Temperature range:** {df['T_C'].min():.0f} deg C to {df['T_C'].max():.0f} deg C
    """)
    return data_path, df, possible_paths


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Gibbs Energy Expressions in TDB Files

    The TDB file contains Gibbs energy parameters. For Cu₂O, the expression is:

    ```
    PARAMETER G(CU2O,CU:O;0) 298.15
        -193230 + 360.057*T - 66.26*T*LN(T)
        - 0.00796*T**2 + 374000*T**(-1);
    ```

    This means:

    $$G^{Cu_2O}(T) = -193230 + 360.057T - 66.26T\ln(T) - 0.00796T^2 + \frac{374000}{T}$$

    The coefficients come from fitting to:
    - Calorimetric data (heat capacity, enthalpy of formation)
    - Phase equilibria (melting points, decomposition temperatures)
    - Oxygen partial pressure measurements

    **This is NOT a linear approximation** — it captures the full temperature dependence of heat capacity.
    """)
    return


@app.cell
def _(df, mo, plt):
    # Create figure showing Gibbs energies
    fig1, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(df['T_C'], df['G_cu2o'] / 1000, label='Cu2O (cuprite)', color='#0077BB', lw=2)
    ax1.plot(df['T_C'], df['G_cuo'] / 1000, label='CuO (tenorite)', color='#EE7733', lw=2)
    ax1.plot(df['T_C'], df['G_cu_ref'] / 1000, label='Cu (fcc)', color='#AA3377', lw=2, ls='--')

    ax1.set_xlabel('Temperature (deg C)', fontsize=12)
    ax1.set_ylabel('Gibbs Energy G (kJ/mol)', fontsize=12)
    ax1.set_title('Gibbs Energy of Cu-O Phases from CALPHAD Database', fontsize=14)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    mo.md(f"""
    ---

    ## Results: Gibbs Energy vs Temperature

    The plot below shows the **absolute Gibbs energy** for each phase.

    Note: These are Gibbs energies relative to the SGTE reference states (defined at 298.15 K).
    """)
    fig1
    return ax1, fig1


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Gibbs Energy of Formation (For Ellingham Diagram)

    For the Ellingham diagram, we need the **Gibbs energy of formation** from the elements:

    **Reaction for Cu2O:**
    $$2\text{Cu}(s) + \frac{1}{2}\text{O}_2(g) \rightarrow \text{Cu}_2\text{O}(s)$$

    $$\Delta G_f^{Cu_2O} = G^{Cu_2O} - 2G^{Cu} - \frac{1}{2}G^{O_2}$$

    **Reaction for CuO:**
    $$\text{Cu}(s) + \frac{1}{2}\text{O}_2(g) \rightarrow \text{CuO}(s)$$

    $$\Delta G_f^{CuO} = G^{CuO} - G^{Cu} - \frac{1}{2}G^{O_2}$$

    **For the Ellingham diagram**, we normalize per mole of O2:
    - Cu2O: multiply by 2 (reaction uses 1/2 mol O2, so x2 gives per mol O2)
    - CuO: multiply by 2 (reaction uses 1/2 mol O2, so x2 gives per mol O2)
    """)
    return


@app.cell
def _(df, mo, np, plt):
    # Create Ellingham-style diagram with ALL oxides
    fig2, ax2 = plt.subplots(figsize=(12, 8))

    # Define oxide data: (column, label, color, linestyle, linewidth)
    # Using colorblind-friendly palette + varying linestyles
    oxides = [
        ('dG_MgO_per_O2',   '2Mg + O2 -> 2MgO',       '#009988', '-',  2.0),   # teal
        ('dG_Al2O3_per_O2', '4/3Al + O2 -> 2/3Al2O3', '#0077BB', '-',  2.0),   # blue
        ('dG_TiO2_per_O2',  'Ti + O2 -> TiO2',        '#AA3377', '-',  2.0),   # purple
        ('dG_SiO2_per_O2',  'Si + O2 -> SiO2',        '#BBBBBB', '-',  2.0),   # gray
        ('dG_FeO_per_O2',   '2Fe + O2 -> 2FeO',       '#CC3311', '-',  2.0),   # red
        ('dG_cu2o_per_O2',  '4Cu + O2 -> 2Cu2O',      '#EE7733', '-',  2.5),   # orange (Cu - thicker)
        ('dG_cuo_per_O2',   '2Cu + O2 -> 2CuO',       '#EE7733', '--', 2.5),   # orange dashed
    ]

    for col, label, color, ls, lw in oxides:
        if col in df.columns:
            ax2.plot(df['T_C'], df[col] / 1000, label=label, color=color, ls=ls, lw=lw)

    # Reference line at dG = 0
    ax2.axhline(y=0, color='black', ls='--', alpha=0.3)

    # Steel melting range (1500-1600 deg C for steelmaking)
    ax2.axvspan(1500, 1650, alpha=0.15, color='orange')
    ax2.text(1575, -100, 'Steelmaking\n(1500-1600C)', ha='center', fontsize=9, color='#CC6600')

    ax2.set_xlabel('Temperature (deg C)', fontsize=12)
    ax2.set_ylabel('dG (kJ/mol O2)', fontsize=12)
    ax2.set_title('Ellingham Diagram: Oxide Stability Comparison', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    ax2.grid(True, which='minor', alpha=0.1)
    ax2.minorticks_on()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Set y-axis to show full range
    ax2.set_ylim(-1200, 100)
    ax2.set_xlim(df['T_C'].min(), df['T_C'].max())

    # Add annotations on right side for key oxides
    T_last = df['T_C'].iloc[-1]
    annotations = [
        ('MgO', df['dG_MgO_per_O2'].iloc[-1]/1000, '#009988'),
        ('Al2O3', df['dG_Al2O3_per_O2'].iloc[-1]/1000, '#0077BB'),
        ('TiO2', df['dG_TiO2_per_O2'].iloc[-1]/1000, '#AA3377'),
        ('SiO2', df['dG_SiO2_per_O2'].iloc[-1]/1000, '#BBBBBB'),
        ('FeO', df['dG_FeO_per_O2'].iloc[-1]/1000, '#CC3311'),
        ('Cu2O', df['dG_cu2o_per_O2'].iloc[-1]/1000, '#EE7733'),
    ]
    for name, y_val, color in annotations:
        ax2.annotate(name, xy=(T_last, y_val), xytext=(T_last + 30, y_val),
                    fontsize=9, fontweight='bold', color=color, va='center')

    plt.subplots_adjust(right=0.90)

    mo.md(f"""
    ---

    ## Ellingham Diagram: Full Oxide Comparison

    This diagram compares the thermodynamic stability of various metal oxides.
    **Lower (more negative) dG = more stable oxide**.

    **Data sources:**
    - **Cu2O, CuO:** pyCALPHAD with Schramm et al. (2005) database — real CALPHAD data
    - **Other oxides:** Linearized approximations from NIST-JANAF tables

    **Key observation:** Cu oxides are at the TOP of the diagram (least negative dG),
    confirming that Cu has the weakest affinity for oxygen among common metals.
    """)
    fig2
    return T_last, annotations, ax2, col, color, fig2, label, ls, lw, name, oxides, y_val


@app.cell
def _(df, mo, np):
    # Extract specific values at key temperatures
    T_1000C_idx = np.abs(df['T_K'] - 1273).argmin()  # 1000°C = 1273K

    T_1000C_idx = int(T_1000C_idx)

    mo.md(f"""
    ---

    ## Numerical Values at Key Temperatures

    **At T = 1000 deg C (1273 K):**

    | Reaction | dG (kJ/mol O2) |
    |----------|-----------------|
    | 4Cu + O2 -> 2Cu2O | {df['dG_cu2o_per_O2'].iloc[T_1000C_idx]/1000:.1f} |
    | 2Cu + O2 -> 2CuO | {df['dG_cuo_per_O2'].iloc[T_1000C_idx]/1000:.1f} |

    **Interpretation:**
    - Negative dG means the oxide formation is thermodynamically favorable
    - Cu oxides have relatively small |dG| compared to Al2O3 (~-1000 kJ/mol O2)
    - This confirms Cu is a "noble" metal — weak affinity for oxygen
    """)
    return (T_1000C_idx,)


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Comparison: Database vs Linear Approximation

    In the other notebook (`cu_ceramic_thermodynamics.py`), we used a linear approximation:

    $$\Delta G_f \approx A + BT$$

    with $A = -170$ kJ/mol, $B = 0.075$ kJ/(mol·K) for Cu2O.

    **The CALPHAD database uses a more complete expression:**

    $$G(T) = a + bT + cT\ln(T) + dT^2 + \frac{e}{T}$$

    The $cT\ln(T)$ term captures **heat capacity variation** with temperature, which the
    linear approximation misses.

    **When does the linear approximation fail?**
    - At very high temperatures (extrapolation)
    - Near phase transitions
    - When heat capacity changes significantly with T

    For screening purposes (comparing oxide stability), the linear approximation is adequate.
    For quantitative predictions (phase diagrams, equilibrium compositions), use CALPHAD databases.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Why Cu Cannot Reduce Al2O3

    Even with proper CALPHAD data, the conclusion remains the same:

    | Oxide | dG at 1000 deg C (kJ/mol O2) | Relative Stability |
    |-------|---------------------------|-------------------|
    | Cu2O | ~-200 | Least stable |
    | FeO | ~-400 | Moderately stable |
    | SiO2 | ~-700 | Very stable |
    | Al2O3 | ~-900 | Extremely stable |
    | MgO | ~-1000 | Most stable |

    **For Cu to reduce Al2O3:**

    $$3\text{Cu} + \text{Al}_2\text{O}_3 \rightarrow \frac{3}{2}\text{Cu}_2\text{O} + 2\text{Al}$$

    For this to proceed, we need:
    $$\Delta G_{rxn} = \frac{3}{2}\Delta G_f^{Cu_2O} - \Delta G_f^{Al_2O_3} < 0$$

    But $\Delta G_f^{Cu_2O} \approx -150$ kJ/mol and $\Delta G_f^{Al_2O_3} \approx -1600$ kJ/mol:
    $$\Delta G_{rxn} \approx \frac{3}{2}(-150) - (-1600) = -225 + 1600 = +1375 \text{ kJ/mol}$$

    **Highly unfavorable!** Cu cannot reduce Al2O3.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---

    ## Summary & Next Steps

    ### What We Learned

    1. **CALPHAD databases** contain assessed Gibbs energy functions (not just linear fits)
    2. **pyCALPHAD** can read TDB files and calculate thermodynamic properties
    3. **Cu oxides are weakly stable** — Cu is "noble" and doesn't easily oxidize
    4. **Cu cannot reduce stable oxides** like Al2O3, MgO, SiO2

    ### For the Honda Project

    Since Cu cannot reduce ceramics, the Cu removal mechanism must be:
    - **Solid solution** (Cu dissolving into ceramic)
    - **Spinel formation** (CuAl2O4)
    - **Surface adsorption**

    ### Next Steps

    1. **Use TC-Python** with TCOX database for Cu-Al-O ternary phase diagrams
    2. Calculate Cu solubility in Al2O3 as f(T)
    3. Identify CuAl2O4 spinel stability region

    ---

    ### Data Source Citation

    > **Database:** Cu-O system, NIMS (2008), based on Schramm et al. (2005)
    > *J. Phase Equilibria and Diffusion*, 26(6), 605-612.
    > DOI: 10.1007/s11669-005-0005-8

    ---
    *MSE 4381 Senior Design | Honda CALPHAD Project | Spring 2026*
    """)
    return


if __name__ == "__main__":
    app.run()
