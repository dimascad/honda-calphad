import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    return mo, np, plt


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
    ## 1. Thermodynamic Framework

    The key question: **Can Cu react favorably with these ceramics?**

    We use Gibbs free energy to answer this:

    $$\Delta G_{rxn} = \sum \Delta G_f (\text{products}) - \sum \Delta G_f (\text{reactants})$$

    - If $\Delta G_{rxn} < 0$: reaction is **thermodynamically favorable**
    - If $\Delta G_{rxn} > 0$: reaction is **unfavorable**

    For oxide systems, we compare stability using the **Ellingham diagram** — plotting $\Delta G_f°$ per mole O₂ vs temperature.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 2. Gibbs Energy Functions

    Standard Gibbs energy of formation follows the form:

    $$\Delta G_f° = \Delta H_f° - T \Delta S_f° \approx A + BT$$

    where:
    - $A \approx \Delta H_f°(298K)$ — standard enthalpy of formation
    - $B \approx -\Delta S_f°$ — negative of standard entropy of formation

    **⚠️ Data Source Note:**
    The values below are **linearized approximations** derived from standard thermodynamic tables.
    The A coefficients match published enthalpies of formation (e.g., Cu₂O: -170.59 kJ/mol from
    Holmes et al. 1989; Al₂O₃: -1675.3 kJ/mol from NIST). The B coefficients were estimated from
    standard entropies. This linearization is valid for limited temperature ranges but does not
    account for heat capacity variations with temperature.

    **For rigorous CALPHAD calculations**, use Thermo-Calc with proper assessed databases (TCOX, SSUB)
    or pyCALPHAD with validated TDB files. See the companion notebook `cu_al_o_pycalphad.py` for
    database-sourced calculations.
    """)
    return


@app.cell
def _(np):
    # ==========================================================================
    # OXIDE THERMODYNAMIC DATA (APPROXIMATE VALUES)
    # ==========================================================================
    # Format: 'name': (A, B, O2_factor, color, linestyle, reaction_str)
    # Model: ΔGf° ≈ A + B·T (kJ/mol), where A ≈ ΔHf°(298K), B ≈ -ΔSf°
    # Normalized by O2_factor for Ellingham diagram (per mole O₂)
    #
    # ⚠️ THESE ARE LINEARIZED APPROXIMATIONS, NOT DATABASE VALUES
    #
    # Data sources for A (enthalpy) coefficients:
    #   Cu₂O: -170.59 kJ/mol — Holmes et al. (1989) J. Chem. Thermodynamics 21:351
    #   CuO:  -156 kJ/mol (approx) — NIST-JANAF, needs verification
    #   FeO:  -272 kJ/mol — NIST-JANAF (wüstite, non-stoichiometric)
    #   Al₂O₃: -1675.7 kJ/mol — NIST WebBook (alpha-corundum)
    #   MgO:  -601.6 kJ/mol — NIST-JANAF
    #   SiO₂: -910.7 kJ/mol — NIST-JANAF (alpha-quartz)
    #   TiO₂: -944.0 kJ/mol — NIST-JANAF (rutile)
    #
    # B coefficients estimated from: B ≈ -ΔSf° = -[S°(oxide) - S°(elements)]
    # These are rough estimates and introduce error at high temperatures.
    # ==========================================================================

    oxide_data = {
        'Cu₂O': (-170, 0.075, 0.5, '#0077BB', '-', '2Cu + ½O₂ → Cu₂O'),
        'CuO': (-155, 0.085, 0.5, '#56B4E9', '--', 'Cu + ½O₂ → CuO'),
        'FeO': (-264, 0.065, 0.5, '#EE7733', '--', 'Fe + ½O₂ → FeO'),
        'Al₂O₃': (-1676, 0.32, 1.5, '#AA3377', ':', '4/3Al + O₂ → 2/3Al₂O₃'),
        'MgO': (-601, 0.11, 0.5, '#009988', '-', '2Mg + O₂ → 2MgO'),
        'SiO₂': (-910, 0.18, 1.0, '#CC3311', '--', 'Si + O₂ → SiO₂'),
        'TiO₂': (-944, 0.18, 1.0, '#E69F00', ':', 'Ti + O₂ → TiO₂'),
    }

    def calc_dGf(name, T_K):
        """Calculate ΔGf at temperature T (K)"""
        A, B, *_ = oxide_data[name]
        return A + B * T_K

    def calc_dGf_per_O2(name, T_K):
        """Calculate ΔGf per mole O₂ for Ellingham diagram"""
        A, B, O2_factor, *_ = oxide_data[name]
        return (A + B * T_K) / O2_factor

    T_K_full = np.linspace(1000, 2100, 200)
    T_C_full = T_K_full - 273
    return T_C_full, T_K_full, calc_dGf_per_O2, oxide_data


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 3. Interactive Ellingham Diagram

    **Use the controls below** to explore oxide stability at different temperatures and select which oxides to compare.
    """)
    return


@app.cell
def _(mo, oxide_data):
    # Temperature slider
    temp_slider = mo.ui.slider(
        start=1000,
        stop=1700,
        step=25,
        value=1600,
        label="🌡️ Temperature (°C)"
    )

    # Oxide multi-select
    oxide_selector = mo.ui.multiselect(
        options=list(oxide_data.keys()),
        value=['Cu₂O', 'FeO', 'Al₂O₃', 'MgO', 'SiO₂', 'TiO₂'],
        label="🧪 Select oxides to display"
    )

    mo.hstack([
        mo.vstack([mo.md("### Temperature"), temp_slider], align="start"),
        mo.vstack([mo.md("### Oxides"), oxide_selector], align="start"),
    ], justify="start", gap=4)
    return oxide_selector, temp_slider


@app.cell
def _(
    T_C_full,
    T_K_full,
    calc_dGf_per_O2,
    np,
    oxide_data,
    oxide_selector,
    plt,
    temp_slider,
):
    _selected = oxide_selector.value if oxide_selector.value else ['Cu₂O']
    _T_mark = temp_slider.value

    _fig, _ax = plt.subplots(figsize=(12, 7))

    # Store line endpoints for direct labeling
    _label_data = []

    for _oxide_name in _selected:
        _A, _B, _O2_factor, _color, _ls, _rxn = oxide_data[_oxide_name]
        _dG_vals = np.array([calc_dGf_per_O2(_oxide_name, T) for T in T_K_full])
        _ax.plot(T_C_full, _dG_vals, linestyle=_ls, color=_color, lw=2.5)

        # Store endpoint for label (right side of plot)
        _label_data.append({
            'name': _oxide_name,
            'y': _dG_vals[-1],  # y-value at right edge
            'color': _color
        })

    # Sort labels by y-position to help with spacing
    _label_data.sort(key=lambda x: x['y'], reverse=True)

    # Add direct labels on right side with spacing to avoid overlap
    _min_spacing = 45  # minimum vertical spacing between labels
    _prev_y = None
    for _ld in _label_data:
        _y_pos = _ld['y']
        # Adjust if too close to previous label
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
    _ax.annotate('Steel\nmelting', xy=(1500, -1150), fontsize=9, color='gray',
                ha='center', va='center', style='italic')

    _ax.set_xlabel('Temperature (°C)', fontsize=12)
    _ax.set_ylabel('ΔG° (kJ/mol O₂)', fontsize=12)
    _ax.set_title('Ellingham Diagram: Oxide Stability', fontsize=14)
    _ax.grid(True, alpha=0.3)
    _ax.set_xlim(1000, 1700)
    _ax.set_ylim(-1200, 0)
    _ax.spines['top'].set_visible(False)
    _ax.spines['right'].set_visible(False)

    # Add extra space on right for labels
    plt.subplots_adjust(right=0.85)
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 4. Stability Rankings at Selected Temperature

    The table below updates based on your temperature selection. **Lower ΔG = more stable**.
    """)
    return


@app.cell
def _(calc_dGf_per_O2, mo, oxide_selector, temp_slider):
    T_K_sel = temp_slider.value + 273
    selected_oxides = oxide_selector.value if oxide_selector.value else ['Cu₂O']

    rankings = [(name, calc_dGf_per_O2(name, T_K_sel)) for name in selected_oxides]
    rankings.sort(key=lambda x: x[1])

    rows = "| Rank | Oxide | ΔGf° (kJ/mol O₂) | Status |\n|:----:|:-----:|:----------------:|:------:|\n"
    for i, (name, dG) in enumerate(rankings, 1):
        if i == 1:
            status = "✅ Most stable"
        elif i == len(rankings):
            status = "⚠️ Least stable"
        else:
            status = ""
        rows += f"| {i} | {name} | {dG:.1f} | {status} |\n"

    mo.md(f"""
    **At T = {temp_slider.value}°C ({T_K_sel} K):**

    {rows}
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 5. Key Insight: Cu Cannot Reduce These Oxides

    From the Ellingham diagram:

    > **Cu₂O is always the LEAST stable oxide in our candidate list.**

    This means Cu **cannot** reduce Al₂O₃, MgO, SiO₂, or TiO₂:

    $$\text{Cu} + \text{Al}_2\text{O}_3 \nrightarrow \text{Cu}_2\text{O} + \text{Al} \quad (\Delta G > 0)$$

    ### So how did last year's team observe Cu capture by Al₂O₃?
    The mechanism must be **different** from oxide reduction.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 6. Actual Cu-Ceramic Interaction Mechanisms

    Since direct reduction is impossible, Cu removal occurs through:

    | Mechanism | How it works | Key factor |
    |-----------|--------------|------------|
    | **Solid Solution** | Cu dissolves into oxide lattice | Temperature (entropy) |
    | **Spinel Formation** | CuO + Al₂O₃ → CuAl₂O₄ | Requires Cu oxidation |
    | **Surface Adsorption** | Cu adsorbs on particle surface | Surface area |
    | **Capillary Penetration** | Molten Cu wets porous ceramics | Porosity |
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 7. Sulfide Exchange Alternative

    From the kickoff meeting, Dr. Zhang showed a **sulfide-based** mechanism. Adjust the temperature to see how it affects the reaction.
    """)
    return


@app.cell
def _(mo):
    sulfide_temp = mo.ui.slider(
        start=1300,
        stop=1700,
        step=25,
        value=1600,
        label="🌡️ Sulfide reaction temperature (°C)"
    )
    sulfide_temp
    return (sulfide_temp,)


@app.cell
def _(mo, sulfide_temp):
    T_sulf = sulfide_temp.value + 273

    # Temperature-dependent approximations
    dGf_FeS = -150 + 0.027 * T_sulf
    dGf_Cu2S = -180 + 0.032 * T_sulf
    dG_rxn = dGf_Cu2S - dGf_FeS

    if dG_rxn < 0:
        result_emoji = "✅"
        result_text = "**FAVORABLE** — Cu₂S is more stable, reaction proceeds"
    else:
        result_emoji = "❌"
        result_text = "**UNFAVORABLE** — reaction will not proceed spontaneously"

    mo.md(f"""
    ### Reaction: 2Cu + FeS → Cu₂S + Fe

    **At T = {sulfide_temp.value}°C ({T_sulf} K):**

    | Species | ΔGf° (kJ/mol) |
    |:-------:|:-------------:|
    | FeS | {dGf_FeS:.1f} |
    | Cu₂S | {dGf_Cu2S:.1f} |

    $$\\Delta G_{{rxn}} = {dGf_Cu2S:.1f} - ({dGf_FeS:.1f}) = {dG_rxn:.1f} \\text{{ kJ/mol}}$$

    {result_emoji} Result: {result_text}
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 8. ⚠️ Model Limitations
    """)
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(r"""
        **This is a simplified screening tool, NOT a rigorous CALPHAD calculation.**

        ### What this model CAN do:
        - Compare relative oxide stability (Ellingham diagram)
        - Show that Cu cannot reduce stable oxides
        - Demonstrate sulfide exchange thermodynamics

        ### What this model CANNOT do:
        - Calculate Cu solubility in oxides
        - Predict phase diagrams or equilibrium assemblages
        - Account for non-ideal mixing (activity coefficients)
        - Model reaction kinetics (how fast things happen)
        - Handle multicomponent interactions (Fe-Cu-Al-O)

        ### Why these limitations matter:
        The **real** Cu capture mechanism involves Cu dissolving into ceramic structures — this requires proper CALPHAD databases with interaction parameters, not just pure component data.
        """),
        kind="warn"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 9. Recommended Next Steps
    """)
    return


@app.cell
def _(mo):
    mo.callout(
        mo.md(r"""
        ### Use Thermo-Calc for Real CALPHAD

        OSU has Thermo-Calc licenses. Key databases:

        | Database | Contents | Use for |
        |----------|----------|---------|
        | **TCFE** | Steel thermodynamics | Cu activity in Fe |
        | **TCOX** | Oxide systems | Cu-Al-O, Cu-Mg-O |
        | **SSUB** | Pure substances | Reference data |

        ### Specific Calculations to Run:

        1. **Cu-Fe binary** — Activity coefficient of Cu in liquid Fe at 1600°C
        2. **Cu-Al-O isothermal section** — Phase diagram at 1600°C
        3. **Cu solubility in Al₂O₃** — vs temperature (1400-1700°C)
        4. **Spinel stability** — CuAl₂O₄ formation conditions

        ### Validate Against Literature:
        - Daehn et al. (2019) — Cu removal mechanisms
        - Last year's senior design report (request from Dr. Zhang)
        """),
        kind="info"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ---
    ## 10. Summary

    | Question | Answer |
    |----------|--------|
    | Can Cu reduce Al₂O₃, MgO, SiO₂, TiO₂? | **No** — Cu oxides are least stable |
    | How does Al₂O₃ capture Cu? | Solid solution, spinel formation, adsorption |
    | Does sulfide exchange work? | **Yes** — FeS + Cu → Cu₂S + Fe is favorable |
    | Is this model sufficient for the project? | **No** — use Thermo-Calc for proper CALPHAD |

    ---
    *MSE 4381 Senior Design | Honda CALPHAD Project | Spring 2026*
    """)
    return


if __name__ == "__main__":
    app.run()
