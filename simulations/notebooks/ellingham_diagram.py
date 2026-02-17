import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from pathlib import Path
    return Path, mo, np, pd, plt


@app.cell
def _(mo):
    mo.md(r"""
    # Cu-Ceramic Thermodynamic Analysis
    ## Honda CALPHAD Project | MSE 4381 Senior Design

    **Objective:** Identify ceramic materials that can remove copper from molten steel during recycling.

    **The Problem:**
    - Recycled steel contains Cu from wiring, motors (0.25-0.3 wt% and rising)
    - Cu causes "hot shortness" (cracking during hot working) above 0.1%
    - No satisfactory industrial-scale Cu removal method exists

    **Our Approach:**
    Use CALPHAD thermodynamics to screen ceramic candidates (Al₂O₃, MgO, TiO₂, SiO₂) for their ability to capture Cu from the melt.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 1. Data Source: Thermo-Calc TCOX14

    **This analysis uses REAL thermodynamic data** extracted from Thermo-Calc's TCOX14 database
    using TC-Python on OSU lab machines.

    The Gibbs energies of formation (ΔGf°) were calculated for each oxide across 500-2000 K:
    - Reference states: pure metals + O₂ gas at 1 atm
    - Normalized per mole O₂ for the Ellingham diagram
    - Individual phase energies extracted (CUPRITE, CORUNDUM, HALITE, etc.)

    **Calculation method:**

    $$\Delta G_f^{\circ} = G_{oxide}^{\circ} - n \cdot G_{metal}^{\circ} - G_{O_2}^{\circ}$$
    """)
    return


@app.cell
def _(Path, pd):
    # Load TC-Python extracted data
    # Try local path first, fall back to GitHub raw URL for Molab
    local_path = Path(__file__).parent.parent.parent / "data" / "tcpython" / "raw" / "oxide_gibbs_energies.csv"
    github_url = "https://raw.githubusercontent.com/dimascad/honda-calphad/main/data/tcpython/raw/oxide_gibbs_energies.csv"

    try:
        if local_path.exists():
            df = pd.read_csv(local_path)
        else:
            df = pd.read_csv(github_url)
    except:
        # Molab fallback - __file__ doesn't exist
        df = pd.read_csv(github_url)

    # Extract relevant columns for Ellingham diagram
    T_K = df['T_K'].values
    T_C = df['T_C'].values

    # dG values in J/mol O2 -> convert to kJ/mol O2
    oxide_dG = {
        'Cu₂O': df['dG_Cu2O_per_O2'].values / 1000,
        'CuO': df['dG_CuO_per_O2'].values / 1000,
        'Al₂O₃': df['dG_Al2O3_per_O2'].values / 1000,
        'MgO': df['dG_MgO_per_O2'].values / 1000,
        'SiO₂': df['dG_SiO2_per_O2'].values / 1000,
        'TiO₂': df['dG_TiO2_per_O2'].values / 1000,
        'FeO': df['dG_FeO_per_O2'].values / 1000,
    }

    # Plotting metadata
    oxide_style = {
        'Cu₂O': {'color': '#0077BB', 'ls': '-', 'reaction': '4Cu + O₂ → 2Cu₂O'},
        'CuO': {'color': '#56B4E9', 'ls': '--', 'reaction': '2Cu + O₂ → 2CuO'},
        'Al₂O₃': {'color': '#AA3377', 'ls': '-', 'reaction': '4/3Al + O₂ → 2/3Al₂O₃'},
        'MgO': {'color': '#009988', 'ls': '-', 'reaction': '2Mg + O₂ → 2MgO'},
        'SiO₂': {'color': '#CC3311', 'ls': '--', 'reaction': 'Si + O₂ → SiO₂'},
        'TiO₂': {'color': '#E69F00', 'ls': ':', 'reaction': 'Ti + O₂ → TiO₂'},
        'FeO': {'color': '#EE7733', 'ls': '--', 'reaction': '2Fe + O₂ → 2FeO'},
    }
    return T_C, T_K, data_path, df, oxide_dG, oxide_style


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 2. Interactive Ellingham Diagram

    **Use the controls below** to explore oxide stability at different temperatures and select which oxides to compare.

    Lower ΔG° = more thermodynamically stable oxide.
    """)
    return


@app.cell
def _(mo, oxide_dG):
    # Temperature slider
    temp_slider = mo.ui.slider(
        start=500,
        stop=1700,
        step=25,
        value=1327,  # ~1600K, typical steelmaking
        label="Temperature (°C)"
    )

    # Oxide multi-select
    oxide_selector = mo.ui.multiselect(
        options=list(oxide_dG.keys()),
        value=['Cu₂O', 'CuO', 'FeO', 'Al₂O₃', 'MgO', 'SiO₂', 'TiO₂'],
        label="Select oxides to display"
    )

    mo.hstack([
        mo.vstack([mo.md("### Temperature"), temp_slider], align="start"),
        mo.vstack([mo.md("### Oxides"), oxide_selector], align="start"),
    ], justify="start", gap=4)
    return oxide_selector, temp_slider


@app.cell
def _(T_C, np, oxide_dG, oxide_selector, oxide_style, plt, temp_slider):
    _selected = oxide_selector.value if oxide_selector.value else ['Cu₂O']
    _T_mark = temp_slider.value

    _fig, _ax = plt.subplots(figsize=(12, 7))

    # Store line endpoints for direct labeling
    _label_data = []

    for _oxide_name in _selected:
        _style = oxide_style[_oxide_name]
        _dG_vals = oxide_dG[_oxide_name]
        _ax.plot(T_C, _dG_vals, linestyle=_style['ls'], color=_style['color'], lw=2.5)

        # Store endpoint for label (right side of plot)
        # Find index closest to 1700°C for label position
        _idx = np.argmin(np.abs(T_C - 1700))
        _label_data.append({
            'name': _oxide_name,
            'y': _dG_vals[_idx],
            'color': _style['color']
        })

    # Sort labels by y-position to help with spacing
    _label_data.sort(key=lambda x: x['y'], reverse=True)

    # Add direct labels on right side with spacing to avoid overlap
    _min_spacing = 45
    _prev_y = None
    for _ld in _label_data:
        _y_pos = _ld['y']
        if _prev_y is not None and abs(_y_pos - _prev_y) < _min_spacing:
            _y_pos = _prev_y - _min_spacing
        _ax.annotate(_ld['name'],
                    xy=(1700, _ld['y']),
                    xytext=(1710, _y_pos),
                    fontsize=10, fontweight='bold',
                    color=_ld['color'],
                    va='center', ha='left',
                    annotation_clip=False)
        _prev_y = _y_pos

    # Temperature marker
    _ax.axvline(x=_T_mark, color='red', linestyle='--', lw=2, alpha=0.8)
    _ax.annotate(f'{_T_mark}°C', xy=(_T_mark, -50), fontsize=10, color='red',
                ha='center', va='bottom', fontweight='bold')

    # Steel melting range
    _ax.axvspan(1400, 1600, alpha=0.12, color='gray')
    _ax.annotate('Steel\nmelting', xy=(1500, -1050), fontsize=9, color='gray',
                ha='center', va='center', style='italic')

    _ax.set_xlabel('Temperature (°C)', fontsize=12)
    _ax.set_ylabel('ΔG° (kJ/mol O₂)', fontsize=12)
    _ax.set_title('Ellingham Diagram: Oxide Stability (TCOX14 Data)', fontsize=14)
    _ax.grid(True, alpha=0.3)
    _ax.set_xlim(200, 1750)
    _ax.set_ylim(-1150, 0)
    _ax.spines['top'].set_visible(False)
    _ax.spines['right'].set_visible(False)

    plt.subplots_adjust(right=0.85)
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 3. Stability Rankings at Selected Temperature

    The table below updates based on your temperature selection. **Lower ΔG = more stable**.
    """)
    return


@app.cell
def _(T_K, mo, np, oxide_dG, oxide_selector, temp_slider):
    _T_K_sel = temp_slider.value + 273
    _selected_oxides = oxide_selector.value if oxide_selector.value else ['Cu₂O']

    # Find closest temperature index
    _idx = np.argmin(np.abs(T_K - _T_K_sel))

    _rankings = [(name, oxide_dG[name][_idx]) for name in _selected_oxides]
    _rankings.sort(key=lambda x: x[1])

    _rows = "| Rank | Oxide | ΔGf° (kJ/mol O₂) | Status |\n|:----:|:-----:|:----------------:|:------:|\n"
    for i, (name, dG) in enumerate(_rankings, 1):
        if i == 1:
            status = "Most stable"
        elif i == len(_rankings):
            status = "Least stable"
        else:
            status = ""
        _rows += f"| {i} | {name} | {dG:.1f} | {status} |\n"

    mo.md(f"""
    **At T = {temp_slider.value}°C ({_T_K_sel} K):**

    {_rows}

    *Gap between Cu₂O and MgO: ~{oxide_dG['MgO'][_idx] - oxide_dG['Cu₂O'][_idx]:.0f} kJ/mol O₂*
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 4. Key Insight: Cu Cannot Reduce These Oxides

    From the Ellingham diagram:

    > **Cu₂O is the LEAST stable oxide among all candidates.**

    This means Cu **cannot** reduce Al₂O₃, MgO, SiO₂, or TiO₂:

    $$\text{Cu} + \text{Al}_2\text{O}_3 \nrightarrow \text{Cu}_2\text{O} + \text{Al} \quad (\Delta G > 0)$$

    The thermodynamic driving force is ~800 kJ/mol O₂ in the WRONG direction.

    ### So what mechanism could remove Cu using ceramics?
    The mechanism must be **different** from oxide reduction. This is an open research question.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 5. Candidate Cu-Ceramic Interaction Mechanisms

    Since direct reduction is thermodynamically impossible, Cu removal would need to occur through an alternative pathway. Possible mechanisms to investigate include:

    | Mechanism | How it would work | Key factor | Status |
    |-----------|-------------------|------------|--------|
    | **Solid Solution** | Cu dissolves into oxide lattice (substitutional or interstitial) | High temperature (entropy-driven) | Unverified |
    | **Spinel Formation** | CuO + Al₂O₃ → CuAl₂O₄ (requires Cu oxidation first) | Oxygen potential | Hypothesis — not yet demonstrated for decopperization |
    | **Surface Adsorption** | Cu atoms adsorb on ceramic particle surfaces | Surface area, porosity | Unverified |
    | **Physical Infiltration** | Fe-Cu melt infiltrates porous ceramic substrate | Porosity, capillary pressure | Observed by Draczuk et al. (2021), but not selective for Cu |

    **Note:** Draczuk et al. (2021) tested ZnAl₂O₄ filters for decopperization of Fe-Cu melts and found limited selectivity. Copper loss was attributed primarily to evaporation, not chemical capture. Both molten Cu and molten Fe are non-wetting on oxide ceramics (contact angles >100°), so selective wetting is not a viable mechanism. These mechanisms remain hypotheses for CALPHAD screening.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 6. Physical Stability: Melting Points

    Cu₂O is also "weak" physically - it melts at much lower temperature than the ceramic candidates:

    | Material | Melting Point (°C) | Status at 1500°C |
    |----------|-------------------|------------------|
    | Cu₂O | 1235 | **Liquid** |
    | CuO | 1326 | **Liquid** |
    | FeO | 1377 | **Liquid** |
    | SiO₂ | 1713 | Solid |
    | TiO₂ | 1843 | Solid |
    | Al₂O₃ | 2072 | Solid |
    | MgO | 2852 | Solid |

    At steelmaking temperatures (1500-1600°C), Cu oxides are molten while the ceramic candidates remain solid particles that can be separated from the melt.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 7. Data Quality Notes

    The TC-Python extraction shows some phase transitions at high temperature:

    - **Cu₂O > 1350°C:** CUPRITE → IONIC_LIQ (melting)
    - **CuO > 1400°C:** CUO → IONIC_LIQ (melting)
    - **FeO > 850°C:** Switches from SPINEL to HALITE phase
    - **SiO₂ > 1150°C:** QUARTZ → TRIDYMITE → CRISTOBALITE (polymorphs)

    At very high temperatures (>1650°C), some solid phases are not stable and the script
    falls back to system energy. This is physically correct - those oxides have melted.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 8. Summary

    | Question | Answer |
    |----------|--------|
    | Can Cu reduce Al₂O₃, MgO, SiO₂, TiO₂? | **No** — Cu₂O is the least stable oxide (~800 kJ/mol O₂ gap) |
    | How might ceramics capture Cu? | Open question — candidates: solid solution, spinel formation, surface adsorption |
    | Which ceramic is most stable? | **MgO** (-987 kJ/mol O₂ at 1000K), then Al₂O₃ (-908) |
    | Do Cu oxides survive steelmaking temps? | **No** — they melt below 1400°C |

    ---
    *MSE 4381 Senior Design | Honda CALPHAD Project | Spring 2026*

    *Data: Thermo-Calc TCOX14 via TC-Python*
    """)
    return


if __name__ == "__main__":
    app.run()
