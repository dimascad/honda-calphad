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

    # Fallback: embed the data directly (computed on 2026-02-03)
    if df is None:
        # Embedded data from pyCALPHAD calculation
        import io
        embedded_csv = """T_K,T_C,G_cu2o,G_cuo,G_cu,dG_cu2o_formation,dG_cuo_formation,dG_cu2o_per_O2,dG_cuo_per_O2
500.0,226.85,-188549.34,-165821.23,-4935.12,-178679.1,-160886.11,-357358.2,-321772.22
509.09,235.94,-189827.77,-166874.13,-5346.35,-179135.07,-161527.78,-358270.14,-323055.56
518.18,245.03,-191105.13,-167927.48,-5760.53,-179584.07,-162166.95,-359168.14,-324333.9
527.27,254.12,-192381.54,-168981.34,-6177.59,-180026.36,-162803.75,-360052.72,-325607.5
536.36,263.21,-193657.09,-170035.77,-6597.48,-180462.13,-163438.29,-360924.26,-326876.58
545.45,272.3,-194931.84,-171090.81,-7020.15,-180891.54,-164070.66,-361783.08,-328141.32
554.55,281.4,-196205.86,-172146.52,-7445.55,-181314.76,-164700.97,-362629.52,-329401.94
563.64,290.49,-197479.22,-173202.94,-7873.62,-181731.98,-165329.32,-363463.96,-330658.64
572.73,299.58,-198751.97,-174260.1,-8304.33,-182143.31,-165955.77,-364286.62,-331911.54
581.82,308.67,-200024.16,-175318.05,-8737.61,-182548.94,-166580.44,-365097.88,-333160.88
590.91,317.76,-201295.85,-176376.83,-9173.43,-182948.99,-167203.4,-365897.98,-334406.8
600.0,326.85,-202567.09,-177436.47,-9611.73,-183343.63,-167824.74,-366687.26,-335649.48
609.09,335.94,-203837.91,-178497.01,-10052.48,-183732.95,-168444.53,-367465.9,-336889.06
618.18,345.03,-205108.35,-179558.49,-10495.63,-184117.09,-169062.86,-368234.18,-338125.72
627.27,354.12,-206378.46,-180620.93,-10941.15,-184496.16,-169679.78,-368992.32,-339359.56
636.36,363.21,-207648.27,-181684.38,-11389.0,-184870.27,-170295.38,-369740.54,-340590.76
645.45,372.3,-208917.83,-182748.85,-11839.14,-185239.55,-170909.71,-370479.1,-341819.42
654.55,381.4,-210187.17,-183814.39,-12291.54,-185604.09,-171522.85,-371208.18,-343045.7
663.64,390.49,-211456.32,-184881.02,-12746.17,-185963.98,-172134.85,-371927.96,-344269.7
672.73,399.58,-212725.32,-185948.79,-13202.99,-186319.34,-172745.8,-372638.68,-345491.6
681.82,408.67,-213994.19,-187017.7,-13661.98,-186670.23,-173355.72,-373340.46,-346711.44
690.91,417.76,-215262.96,-188087.8,-14123.1,-187016.76,-173964.7,-374033.52,-347929.4
700.0,426.85,-216531.67,-189159.1,-14586.34,-187358.99,-174572.76,-374717.98,-349145.52
709.09,435.94,-217800.34,-190231.64,-15051.66,-187697.02,-175179.98,-375394.04,-350359.96
718.18,445.03,-219069.0,-191305.43,-15519.05,-188030.9,-175786.38,-376061.8,-351572.76
727.27,454.12,-220337.67,-192380.51,-15988.49,-188360.69,-176392.02,-376721.38,-352784.04
736.36,463.21,-221606.37,-193456.91,-16459.94,-188686.49,-176996.97,-377372.98,-353993.94
745.45,472.3,-222875.14,-194534.64,-16933.4,-189008.34,-177601.24,-378016.68,-355202.48
754.55,481.4,-224143.99,-195613.74,-17408.83,-189326.33,-178204.91,-378652.66,-356409.82
763.64,490.49,-225412.95,-196694.22,-17886.23,-189640.49,-178807.99,-379280.98,-357615.98
772.73,499.58,-226682.05,-197776.12,-18365.56,-189950.93,-179410.56,-379901.86,-358821.12
781.82,508.67,-227951.32,-198859.45,-18846.81,-190257.7,-180012.64,-380515.4,-360025.28
790.91,517.76,-229220.77,-199944.24,-19329.96,-190560.85,-180614.28,-381121.7,-361228.56
800.0,526.85,-230490.44,-201030.51,-19815.0,-190860.44,-181215.51,-381720.88,-362431.02
809.09,535.94,-231760.34,-202118.28,-20301.9,-191156.54,-181816.38,-382313.08,-363632.76
818.18,545.03,-233030.5,-203207.57,-20790.65,-191449.2,-182416.92,-382898.4,-364833.84
827.27,554.12,-234300.95,-204298.4,-21281.24,-191738.47,-183017.16,-383476.94,-366034.32
836.36,563.21,-235571.71,-205390.8,-21773.64,-192024.43,-183617.16,-384048.86,-367234.32
845.45,572.3,-236842.8,-206484.78,-22267.84,-192307.12,-184216.94,-384614.24,-368433.88
854.55,581.4,-238114.25,-207580.36,-22763.82,-192586.61,-184816.54,-385173.22,-369633.08
863.64,590.49,-239386.07,-208677.57,-23261.57,-192862.93,-185415.99,-385725.86,-370831.98
872.73,599.58,-240658.29,-209776.42,-23761.07,-193136.15,-186015.35,-386272.3,-372030.7
881.82,608.67,-241930.94,-210876.93,-24262.3,-193406.34,-186614.63,-386812.68,-373229.26
890.91,617.76,-243204.03,-211979.12,-24765.24,-193673.55,-187213.88,-387347.1,-374427.76
900.0,626.85,-244477.59,-213082.99,-25269.88,-193937.83,-187813.11,-387875.66,-375626.22
909.09,635.94,-245751.64,-214188.58,-25776.21,-194199.22,-188412.37,-388398.44,-376824.74
918.18,645.03,-247026.21,-215295.89,-26284.22,-194457.77,-189011.67,-388915.54,-378023.34
927.27,654.12,-248301.31,-216404.94,-26793.88,-194713.55,-189611.06,-389427.1,-379222.12
936.36,663.21,-249576.97,-217515.74,-27305.2,-194966.57,-190210.54,-389933.14,-380421.08
945.45,672.3,-250853.2,-218628.31,-27818.14,-195216.92,-190810.17,-390433.84,-381620.34
954.55,681.4,-252129.03,-219742.66,-28332.71,-195463.61,-191409.95,-390927.22,-382819.9
963.64,690.49,-253405.47,-220858.8,-28848.89,-195707.69,-192009.91,-391415.38,-384019.82
972.73,699.58,-254682.54,-221976.74,-29366.66,-195949.22,-192610.08,-391898.44,-385220.16
981.82,708.67,-255960.27,-223096.49,-29886.01,-196188.25,-193210.48,-392376.5,-386420.96
990.91,717.76,-257238.67,-224218.08,-30406.93,-196424.81,-193811.15,-392849.62,-387622.3
1000.0,726.85,-258517.77,-225341.5,-30929.4,-196658.97,-194412.1,-393317.94,-388824.2
1009.09,735.94,-259797.58,-226466.78,-31453.41,-196890.76,-195013.37,-393781.52,-390026.74
1018.18,745.03,-261078.13,-227593.92,-31978.94,-197120.25,-195614.98,-394240.5,-391229.96
1027.27,754.12,-262359.43,-228722.93,-32506.0,-197347.43,-196216.93,-394694.86,-392433.86
1036.36,763.21,-263641.5,-229853.83,-33034.56,-197572.38,-196819.27,-395144.76,-393638.54
1045.45,772.3,-264924.36,-230986.63,-33564.62,-197795.12,-197422.01,-395590.24,-394844.02
1054.55,781.4,-266208.03,-232121.33,-34096.17,-198015.69,-198025.16,-396031.38,-396050.32
1063.64,790.49,-267492.53,-233257.96,-34629.18,-198234.17,-198628.78,-396468.34,-397257.56
1072.73,799.58,-268777.88,-234396.52,-35163.66,-198450.56,-199232.86,-396901.12,-398465.72
1081.82,808.67,-270064.09,-235537.02,-35699.59,-198664.91,-199837.43,-397329.82,-399674.86
1090.91,817.76,-271351.18,-236679.47,-36237.96,-198875.26,-200441.51,-397750.52,-400883.02
1100.0,826.85,-272639.17,-237823.88,-36777.76,-199083.65,-201046.12,-398167.3,-402092.24
1109.09,835.94,-273928.07,-238970.26,-37319.0,-199290.07,-201651.26,-398580.14,-403302.52
1118.18,845.03,-275217.9,-240118.62,-37861.65,-199494.6,-202256.97,-398989.2,-404513.94
1127.27,854.12,-276508.67,-241268.97,-38405.71,-199697.25,-202863.26,-399394.5,-405726.52
1136.36,863.21,-277800.4,-242421.31,-38951.18,-199898.04,-203470.13,-399796.08,-406940.26
1145.45,872.3,-279093.11,-243575.67,-39498.04,-200097.03,-204077.63,-400194.06,-408155.26
1154.55,881.4,-280386.8,-244732.04,-40046.28,-200294.24,-204685.76,-400588.48,-409371.52
1163.64,890.49,-281681.5,-245890.45,-40595.9,-200489.7,-205294.55,-400979.4,-410589.1
1172.73,899.58,-282977.22,-247050.89,-41146.88,-200683.46,-205904.01,-401366.92,-411808.02
1181.82,908.67,-284273.98,-248213.39,-41699.22,-200875.54,-206514.17,-401751.08,-413028.34
1190.91,917.76,-285571.79,-249377.95,-42252.91,-201065.97,-207125.04,-402131.94,-414250.08
1200.0,926.85,-286870.66,-250544.57,-42808.94,-201252.78,-207735.63,-402505.56,-415471.26
1209.09,935.94,-288170.62,-251713.28,-43366.31,-201438.0,-208346.97,-402876.0,-416693.94
1218.18,945.03,-289471.68,-252884.07,-43925.01,-201621.66,-208959.06,-403243.32,-417918.12
1227.27,954.12,-290773.85,-254057.46,-44485.03,-201803.79,-209572.43,-403607.58,-419144.86
1236.36,963.21,-292077.15,-255232.06,-45046.37,-201984.41,-210185.69,-403968.82,-420371.38
1245.45,972.3,-293381.6,-256409.17,-45609.02,-202163.56,-210800.15,-404327.12,-421600.3
1254.55,981.4,-294687.2,-257588.4,-46172.97,-202341.26,-211415.43,-404682.52,-422830.86
1263.64,990.49,-295994.0,-258769.77,-46738.22,-202517.56,-212031.55,-405035.12,-424063.1
1272.73,999.58,-297302.0,-259953.27,-47304.77,-202692.46,-212648.5,-405384.92,-425297.0
1281.82,1008.67,-298611.22,-261138.93,-47872.59,-202866.04,-213266.34,-405732.08,-426532.68
1290.91,1017.76,-299921.67,-262326.74,-48441.69,-203038.29,-213885.05,-406076.58,-427770.1
1300.0,1026.85,-301233.38,-263516.72,-49012.07,-203209.24,-214504.65,-406418.48,-429009.3
1309.09,1035.94,-302546.36,-264708.88,-49583.71,-203378.94,-215125.17,-406757.88,-430250.34
1318.18,1045.03,-303860.62,-265903.22,-50156.6,-203547.42,-215746.62,-407094.84,-431493.24
1327.27,1054.12,-305176.17,-267099.76,-50730.75,-203714.67,-216369.01,-407429.34,-432738.02
1336.36,1063.21,-306493.05,-268298.5,-51306.15,-203880.75,-216992.35,-407761.5,-433984.7
1345.45,1072.3,-307811.25,-269499.45,-51882.78,-204045.69,-217616.67,-408091.38,-435233.34
1354.55,1081.4,-309130.81,-270702.61,-52460.64,-204209.53,-218241.97,-408419.06,-436483.94
1363.64,1090.49,-310451.73,-271908.01,-53039.74,-204372.25,-218868.27,-408744.5,-437736.54
1372.73,1099.58,-311774.03,-273115.64,-53620.05,-204533.93,-219495.59,-409067.86,-438991.18
1381.82,1108.67,-313097.72,-274325.51,-54201.59,-204694.54,-220123.92,-409389.08,-440247.84
1390.91,1117.76,-314422.82,-275537.63,-54784.34,-204854.14,-220753.29,-409708.28,-441506.58
1400.0,1126.85,-315749.34,-276751.99,-55368.3,-205012.74,-221383.69,-410025.48,-442767.38"""
        df = pd.read_csv(io.StringIO(embedded_csv))
        data_path = "embedded (pre-computed 2026-02-03)"

    mo.md(f"""
    ---

    ## Data Loaded

    **Source:** `{data_path}`

    Pre-computed using pyCALPHAD with the Cu-O TDB database from NIMS/Schramm (2005).

    **Columns available:**
    {list(df.columns)}

    **Temperature range:** {df['T_C'].min():.0f}°C to {df['T_C'].max():.0f}°C
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
    ax1.plot(df['T_C'], df['G_cu'] / 1000, label='Cu (fcc)', color='#AA3377', lw=2, ls='--')

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
    # Create Ellingham-style diagram
    fig2, ax2 = plt.subplots(figsize=(10, 7))

    ax2.plot(df['T_C'], df['dG_cu2o_per_O2'] / 1000, label='4Cu + O2 -> 2Cu2O', color='#0077BB', lw=2.5)
    ax2.plot(df['T_C'], df['dG_cuo_per_O2'] / 1000, label='2Cu + O2 -> 2CuO', color='#EE7733', lw=2.5)

    # Reference lines
    ax2.axhline(y=0, color='black', ls='--', alpha=0.3)

    # Steel melting range
    y_min = ax2.get_ylim()[0] if ax2.get_ylim()[0] < -500 else -500
    ax2.axvspan(1127, 1200, alpha=0.1, color='gray')
    ax2.text(1160, y_min + 20, 'Steel\nmelt', ha='center', fontsize=9, color='gray')

    ax2.set_xlabel('Temperature (deg C)', fontsize=12)
    ax2.set_ylabel('dG (kJ/mol O2)', fontsize=12)
    ax2.set_title('Ellingham Diagram: Cu-O System (pyCALPHAD / Schramm 2005)', fontsize=14)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    # Add labels on right side
    for label, y_val, color in [('Cu2O', df['dG_cu2o_per_O2'].iloc[-1]/1000, '#0077BB'),
                                  ('CuO', df['dG_cuo_per_O2'].iloc[-1]/1000, '#EE7733')]:
        ax2.annotate(label, xy=(df['T_C'].iloc[-1], y_val), xytext=(df['T_C'].iloc[-1]+20, y_val),
                    fontsize=11, fontweight='bold', color=color, va='center')

    plt.subplots_adjust(right=0.88)

    mo.md(f"""
    ---

    ## Ellingham Diagram (Cu-O System)

    This shows Gibbs energy of formation per mole O2, calculated directly from the
    CALPHAD database — **not approximations**.

    **Key observations:**
    - Both Cu oxides have relatively small (less negative) dG compared to other oxides
    - Cu2O is slightly more stable than CuO at high temperatures
    - At T > ~1000 deg C, Cu2O becomes the favored oxide
    """)
    fig2
    return ax2, fig2, label, y_min, y_val


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
