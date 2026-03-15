import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import math
    import matplotlib.pyplot as plt
    return math, mo, np, plt


# ── Constants (no output) ────────────────────────────────────────────

@app.cell
def _(np):
    OXIDES = {
        "Fe₂O₃": {
            "product": "CuFe₂O₄",
            "dG_1800K_kJ": -111.9,
            "MW_oxide": 159.69,
            "rho": 5240,
            "cu_per_mol": 1,
            "mp_C": 1565,
            "tier": "Strong",
            "notes": "Top candidate. CuFe₂O₄ spinel persists to 1700K.",
        },
        "V₂O₅": {
            "product": "Cu₃V₂O₈",
            "dG_1800K_kJ": -109.2,
            "MW_oxide": 181.88,
            "rho": 3357,
            "cu_per_mol": 3,
            "mp_C": 690,
            "tier": "Strong",
            "notes": "Strong driving force. 3 Cu per mol (most efficient). Low mp.",
        },
        "MnO": {
            "product": "CuMn₂O₄",
            "dG_1800K_kJ": -63.5,
            "MW_oxide": 70.94,
            "rho": 5430,
            "cu_per_mol": 0.5,
            "mp_C": 1945,
            "tier": "Strong",
            "notes": "Spinel product. High melting point. Needs 2 mol per mol Cu.",
        },
        "SiO₂": {
            "product": "Cu₂SiO₄",
            "dG_1800K_kJ": -50.2,
            "MW_oxide": 60.08,
            "rho": 2650,
            "cu_per_mol": 2,
            "mp_C": 1713,
            "tier": "Strong",
            "notes": "Cheap, abundant. Product dissolves into slag.",
        },
        "Al₂O₃": {
            "product": "CuAl₂O₄",
            "dG_1800K_kJ": -35.7,
            "MW_oxide": 101.96,
            "rho": 3950,
            "cu_per_mol": 1,
            "mp_C": 2072,
            "tier": "Moderate",
            "notes": "Tested Year 2. CuAl₂O₄ spinel confirmed by Zhang.",
        },
    }

    MW_CU = 63.546
    D_CU_LIQUID = 9.63e-10

    # DICTRA temperature sweep: [temp_K, radius_um, time_s, cu_captured_mg]
    # 11 temperatures (1673-1923K), 5 radii, 4 times = 220 rows
    DICTRA_DATA = np.array([
        [1673, 25, 60, 4.9146e-05], [1673, 25, 300, 4.9472e-05],
        [1673, 25, 600, 4.9879e-05], [1673, 25, 1800, 5.1482e-05],
        [1673, 50, 60, 9.2356e-05], [1673, 50, 300, 9.2850e-05],
        [1673, 50, 600, 9.3465e-05], [1673, 50, 1800, 9.5883e-05],
        [1673, 100, 60, 0.00021934], [1673, 100, 300, 0.00022028],
        [1673, 100, 600, 0.00022145], [1673, 100, 1800, 0.00022604],
        [1673, 250, 60, 0.00092479], [1673, 250, 300, 0.00092799],
        [1673, 250, 600, 0.00093195], [1673, 250, 1800, 0.0009474],
        [1673, 500, 60, 0.0031822], [1673, 500, 300, 0.0031922],
        [1673, 500, 600, 0.0032045], [1673, 500, 1800, 0.0032526],
        [1698, 25, 60, 4.9174e-05], [1698, 25, 300, 4.9611e-05],
        [1698, 25, 600, 5.0154e-05], [1698, 25, 1800, 5.229e-05],
        [1698, 50, 60, 9.2398e-05], [1698, 50, 300, 9.3060e-05],
        [1698, 50, 600, 9.3881e-05], [1698, 50, 1800, 9.7096e-05],
        [1698, 100, 60, 0.00021942], [1698, 100, 300, 0.00022068],
        [1698, 100, 600, 0.00022225], [1698, 100, 1800, 0.00022833],
        [1698, 250, 60, 0.00092507], [1698, 250, 300, 0.00092935],
        [1698, 250, 600, 0.00093463], [1698, 250, 1800, 0.00095507],
        [1698, 500, 60, 0.0031831], [1698, 500, 300, 0.0031964],
        [1698, 500, 600, 0.0032129], [1698, 500, 1800, 0.0032764],
        [1723, 25, 60, 4.9210e-05], [1723, 25, 300, 4.9790e-05],
        [1723, 25, 600, 5.0509e-05], [1723, 25, 1800, 5.3327e-05],
        [1723, 50, 60, 9.2453e-05], [1723, 50, 300, 9.3332e-05],
        [1723, 50, 600, 9.4418e-05], [1723, 50, 1800, 9.8647e-05],
        [1723, 100, 60, 0.00021953], [1723, 100, 300, 0.00022120],
        [1723, 100, 600, 0.00022327], [1723, 100, 1800, 0.00023125],
        [1723, 250, 60, 0.00092542], [1723, 250, 300, 0.00093109],
        [1723, 250, 600, 0.00093807], [1723, 250, 1800, 0.00096479],
        [1723, 500, 60, 0.0031842], [1723, 500, 300, 0.0032019],
        [1723, 500, 600, 0.0032236], [1723, 500, 1800, 0.0033064],
        [1748, 25, 60, 4.9256e-05], [1748, 25, 300, 5.0020e-05],
        [1748, 25, 600, 5.0965e-05], [1748, 25, 1800, 5.4643e-05],
        [1748, 50, 60, 9.2523e-05], [1748, 50, 300, 9.3679e-05],
        [1748, 50, 600, 9.5105e-05], [1748, 50, 1800, 0.00010061],
        [1748, 100, 60, 0.00021966], [1748, 100, 300, 0.00022186],
        [1748, 100, 600, 0.00022457], [1748, 100, 1800, 0.00023492],
        [1748, 250, 60, 0.00092588], [1748, 250, 300, 0.00093333],
        [1748, 250, 600, 0.00094245], [1748, 250, 1800, 0.00097695],
        [1748, 500, 60, 0.0031856], [1748, 500, 300, 0.0032088],
        [1748, 500, 600, 0.0032372], [1748, 500, 1800, 0.0033440],
        [1773, 25, 60, 4.9315e-05], [1773, 25, 300, 5.0313e-05],
        [1773, 25, 600, 5.1542e-05], [1773, 25, 1800, 5.6296e-05],
        [1773, 50, 60, 9.2613e-05], [1773, 50, 300, 9.4121e-05],
        [1773, 50, 600, 9.5974e-05], [1773, 50, 1800, 0.00010306],
        [1773, 100, 60, 0.00021983], [1773, 100, 300, 0.00022270],
        [1773, 100, 600, 0.00022622], [1773, 100, 1800, 0.00023948],
        [1773, 250, 60, 0.00092646], [1773, 250, 300, 0.00093617],
        [1773, 250, 600, 0.00094798], [1773, 250, 1800, 0.00099195],
        [1773, 500, 60, 0.0031874], [1773, 500, 300, 0.0032177],
        [1773, 500, 600, 0.0032544], [1773, 500, 1800, 0.0033901],
        [1798, 25, 60, 4.9390e-05], [1798, 25, 300, 5.0682e-05],
        [1798, 25, 600, 5.2269e-05], [1798, 25, 1800, 5.8350e-05],
        [1798, 50, 60, 9.2727e-05], [1798, 50, 300, 9.4678e-05],
        [1798, 50, 600, 9.7064e-05], [1798, 50, 1800, 0.00010608],
        [1798, 100, 60, 0.00022005], [1798, 100, 300, 0.00022376],
        [1798, 100, 600, 0.00022827], [1798, 100, 1800, 0.00024507],
        [1798, 250, 60, 0.00092719], [1798, 250, 300, 0.00093973],
        [1798, 250, 600, 0.00095487], [1798, 250, 1800, 0.0010102],
        [1798, 500, 60, 0.0031897], [1798, 500, 300, 0.0032288],
        [1798, 500, 600, 0.0032757], [1798, 500, 1800, 0.0034458],
        [1823, 25, 60, 0.0022380], [1823, 25, 300, 0.010131],
        [1823, 25, 600, 0.019790], [1823, 25, 1800, 0.058044],
        [1823, 50, 60, 0.0025091], [1823, 50, 300, 0.010674],
        [1823, 50, 600, 0.020537], [1823, 50, 1800, 0.059394],
        [1823, 100, 60, 0.0031494], [1823, 100, 300, 0.011880],
        [1823, 100, 600, 0.022158], [1823, 100, 1800, 0.062241],
        [1823, 250, 60, 0.0058556], [1823, 250, 300, 0.016450],
        [1823, 250, 600, 0.028051], [1823, 250, 1800, 0.071965],
        [1823, 500, 60, 0.012984], [1823, 500, 300, 0.027245],
        [1823, 500, 600, 0.041299], [1823, 500, 1800, 0.092110],
        [1848, 25, 60, 0.0023281], [1848, 25, 300, 0.010560],
        [1848, 25, 600, 0.020641], [1848, 25, 1800, 0.060575],
        [1848, 50, 60, 0.0026040], [1848, 50, 300, 0.011114],
        [1848, 50, 600, 0.021403], [1848, 50, 1800, 0.061962],
        [1848, 100, 60, 0.0032547], [1848, 100, 300, 0.012342],
        [1848, 100, 600, 0.023056], [1848, 100, 1800, 0.064887],
        [1848, 250, 60, 0.0059963], [1848, 250, 300, 0.016983],
        [1848, 250, 600, 0.029048], [1848, 250, 1800, 0.074851],
        [1848, 500, 60, 0.013198], [1848, 500, 300, 0.027909],
        [1848, 500, 600, 0.042477], [1848, 500, 1800, 0.095424],
        [1873, 25, 60, 0.0024194], [1873, 25, 300, 0.010997],
        [1873, 25, 600, 0.021504], [1873, 25, 1800, 0.063144],
        [1873, 50, 60, 0.0027002], [1873, 50, 300, 0.011561],
        [1873, 50, 600, 0.022282], [1873, 50, 1800, 0.064571],
        [1873, 100, 60, 0.0033611], [1873, 100, 300, 0.012811],
        [1873, 100, 600, 0.023966], [1873, 100, 1800, 0.067573],
        [1873, 250, 60, 0.0061379], [1873, 250, 300, 0.017521],
        [1873, 250, 600, 0.030057], [1873, 250, 1800, 0.077780],
        [1873, 500, 60, 0.013412], [1873, 500, 300, 0.028579],
        [1873, 500, 600, 0.043668], [1873, 500, 1800, 0.098789],
        [1898, 25, 60, 0.0025119], [1898, 25, 300, 0.011439],
        [1898, 25, 600, 0.022380], [1898, 25, 1800, 0.065752],
        [1898, 50, 60, 0.0027976], [1898, 50, 300, 0.012014],
        [1898, 50, 600, 0.023173], [1898, 50, 1800, 0.067217],
        [1898, 100, 60, 0.0034687], [1898, 100, 300, 0.013285],
        [1898, 100, 600, 0.024889], [1898, 100, 1800, 0.070299],
        [1898, 250, 60, 0.0062801], [1898, 250, 300, 0.018065],
        [1898, 250, 600, 0.031079], [1898, 250, 1800, 0.080753],
        [1898, 500, 60, 0.013626], [1898, 500, 300, 0.029252],
        [1898, 500, 600, 0.044870], [1898, 500, 1800, 0.10220],
        [1923, 25, 60, 0.0026056], [1923, 25, 300, 0.011888],
        [1923, 25, 600, 0.023268], [1923, 25, 1800, 0.068396],
        [1923, 50, 60, 0.0028961], [1923, 50, 300, 0.012473],
        [1923, 50, 600, 0.024077], [1923, 50, 1800, 0.069901],
        [1923, 100, 60, 0.0035773], [1923, 100, 300, 0.013766],
        [1923, 100, 600, 0.025824], [1923, 100, 1800, 0.073063],
        [1923, 250, 60, 0.0064231], [1923, 250, 300, 0.018614],
        [1923, 250, 600, 0.032113], [1923, 250, 1800, 0.083767],
        [1923, 500, 60, 0.013840], [1923, 500, 300, 0.029929],
        [1923, 500, 600, 0.046083], [1923, 500, 1800, 0.10566],
    ])

    AVAIL_TEMPS = sorted(set(DICTRA_DATA[:, 0].astype(int).tolist()))
    AVAIL_RADII = sorted(set(DICTRA_DATA[:, 1].astype(int).tolist()))

    return D_CU_LIQUID, DICTRA_DATA, MW_CU, OXIDES, AVAIL_TEMPS, AVAIL_RADII


# ── Story sequence definition ───────────────────────────────────────

@app.cell
def _():
    # (temp_K, radius_um, oxide_dose_g, narrative, active_param)
    # active_param: which slider is "moving" this frame
    _temps = [1673, 1698, 1723, 1748, 1773, 1798, 1823, 1848, 1873, 1898, 1923]
    _radii = [500, 250, 100, 50, 25]
    _tlabels = {60: "1 min", 300: "5 min", 600: "10 min", 1800: "30 min"}

    STORY = []

    # Phase 1: Temperature sweep at R=250, dose=2g
    for _T in _temps:
        _tag = "LIQUID" if _T >= 1823 else "SOLID"
        STORY.append({
            "T": _T, "R": 250, "dose": 2.0,
            "narrative": f"Step 1 / Temperature: {_T} K ({_tag})",
            "active": "temp",
        })

    # Phase 2: Radius sweep at T=1923, dose=2g
    for _R in _radii:
        STORY.append({
            "T": 1923, "R": _R, "dose": 2.0,
            "narrative": f"Step 2 / Particle radius: {_R} um",
            "active": "radius",
        })

    # Phase 3: Dose sweep at T=1923, R=25
    for _dose in [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]:
        STORY.append({
            "T": 1923, "R": 25, "dose": _dose,
            "narrative": f"Step 3 / Oxide dose: {_dose:.1f} g",
            "active": "dose",
        })

    # Finale
    for _ in range(4):
        STORY.append({
            "T": 1923, "R": 25, "dose": 5.0,
            "narrative": "OPTIMAL: T=1923 K, R=25 um, 5g Fe2O3",
            "active": "optimal",
        })

    STORY_LEN = len(STORY)
    return STORY, STORY_LEN


# ── Story state ──────────────────────────────────────────────────────

@app.cell
def _(mo):
    get_idx, set_idx = mo.state(0, allow_self_loops=True)
    return get_idx, set_idx


# ── Compute current story frame (isolates state read) ────────────────

@app.cell
def _(get_idx, STORY):
    _i = get_idx()
    story_frame = STORY[_i % len(STORY)]
    return (story_frame,)


# ── Story controls ───────────────────────────────────────────────────

@app.cell
def _(mo):
    story_toggle = mo.ui.switch(label="Story Mode", value=False)
    story_speed = mo.ui.refresh(
        options=["0.25s", "0.5s", "0.75s", "1s", "1.5s", "2s", "3s"],
        default_interval="1s",
        label="Speed"
    )
    return story_toggle, story_speed


# ── Auto-advance ─────────────────────────────────────────────────────

@app.cell
def _(story_toggle, story_speed, set_idx, STORY_LEN):
    _tick = story_speed  # re-run on each tick
    if story_toggle.value:
        set_idx(lambda i: (i + 1) % STORY_LEN)
    return


# ── Sliders (recreated with story values when active) ────────────────

@app.cell
def _(mo, OXIDES, AVAIL_TEMPS, story_toggle, story_frame):
    # When story mode is on, sliders are created with story values
    # so the thumb visually jumps to the new position each tick.
    # When off, sliders use defaults and user controls them.

    _sf = story_frame if story_toggle.value else None

    oxide_dropdown = mo.ui.dropdown(
        options=list(OXIDES.keys()),
        value="Fe₂O₃",
        label="Oxide"
    )
    temp_slider = mo.ui.slider(
        start=min(AVAIL_TEMPS), stop=max(AVAIL_TEMPS), step=25,
        value=_sf["T"] if _sf else 1823,
        label="Temperature (K)"
    )
    steel_mass_slider = mo.ui.slider(
        start=0.1, stop=2.0, step=0.1, value=0.5,
        label="Steel (kg)"
    )
    cu_init_slider = mo.ui.slider(
        start=0.10, stop=0.50, step=0.01, value=0.30,
        label="Cu initial (wt%)"
    )
    cu_target_slider = mo.ui.slider(
        start=0.05, stop=0.25, step=0.01, value=0.10,
        label="Cu target (wt%)"
    )
    oxide_mass_slider = mo.ui.slider(
        start=0.5, stop=20.0, step=0.5,
        value=_sf["dose"] if _sf else 5.0,
        label="Oxide dose (g)"
    )
    particle_radius_slider = mo.ui.slider(
        start=25, stop=500, step=25,
        value=_sf["R"] if _sf else 100,
        label="Particle R (um)"
    )

    return (
        cu_init_slider, cu_target_slider, oxide_dropdown,
        oxide_mass_slider, particle_radius_slider, steel_mass_slider,
        temp_slider,
    )


# ── Control panel layout ─────────────────────────────────────────────

@app.cell
def _(mo, oxide_dropdown, temp_slider, steel_mass_slider,
      cu_init_slider, cu_target_slider, oxide_mass_slider,
      particle_radius_slider, story_toggle, story_speed,
      story_frame):

    _is_story = story_toggle.value
    _active = story_frame["active"] if _is_story else None

    # Highlight the active slider's label during story mode
    def _label(name, param):
        if _active == param:
            return f"**>>> {name} <<<**"
        return name

    _story_bar = mo.hstack([
        story_toggle,
        story_speed if _is_story else mo.md(""),
        mo.md(f'*{story_frame["narrative"]}*') if _is_story else mo.md(""),
    ], justify="start", gap=1.0, align="center")

    mo.vstack([
        mo.md("# Cu Removal — Experiment Designer"),
        _story_bar,
        mo.hstack([oxide_dropdown, temp_slider, steel_mass_slider],
                  justify="start", gap=0.5),
        mo.hstack([cu_init_slider, cu_target_slider,
                   oxide_mass_slider, particle_radius_slider],
                  justify="start", gap=0.5),
    ])
    return


# ── Core calculation ─────────────────────────────────────────────────

@app.cell
def _(
    math, np, MW_CU, OXIDES, DICTRA_DATA, AVAIL_TEMPS,
    oxide_dropdown, steel_mass_slider, cu_init_slider,
    cu_target_slider, oxide_mass_slider, particle_radius_slider,
    temp_slider,
):
    _ox = OXIDES[oxide_dropdown.value]
    _steel_kg = steel_mass_slider.value
    _cu_init = cu_init_slider.value
    _cu_target = cu_target_slider.value
    _oxide_g = oxide_mass_slider.value
    _r_um = particle_radius_slider.value
    _temp_K = temp_slider.value

    # Determine phase
    _phase = "LIQUID" if _temp_K >= 1823 else "FCC_A1 (solid)"

    _cu_remove_g = _steel_kg * 1000 * (_cu_init - _cu_target) / 100
    _cu_remove_mol = _cu_remove_g / MW_CU
    _oxide_stoich_g = (_cu_remove_mol / _ox["cu_per_mol"]) * _ox["MW_oxide"]
    _excess = _oxide_g / _oxide_stoich_g if _oxide_stoich_g > 0 else 0

    _r_m = _r_um * 1e-6
    _v_p = (4/3) * math.pi * _r_m**3
    _m_p_g = _ox["rho"] * _v_p * 1000
    _n_particles = _oxide_g / _m_p_g
    _area_cm2 = _n_particles * 4 * math.pi * _r_m**2 * 1e4
    _t_diff = _r_m**2 / (2 * 9.63e-10)

    # DICTRA lookup: closest temp and radius
    _closest_t = min(AVAIL_TEMPS, key=lambda x: abs(x - _temp_K))
    _avail_r = sorted(set(DICTRA_DATA[:, 1].astype(int)))
    _closest_r = min(_avail_r, key=lambda x: abs(x - _r_um))
    _mask = (DICTRA_DATA[:, 0] == _closest_t) & (DICTRA_DATA[:, 1] == _closest_r)
    _d_times = DICTRA_DATA[_mask, 2]
    _d_capture = DICTRA_DATA[_mask, 3]

    _total_cu_mg = _steel_kg * 1000 * _cu_init / 100 * 1000
    _removal_pct = np.minimum(_d_capture * _n_particles / _total_cu_mg * 100, 100)

    _target_pct = (_cu_init - _cu_target) / _cu_init * 100
    _time_to_target = None
    for _i in range(len(_removal_pct)):
        if _removal_pct[_i] >= _target_pct:
            if _i == 0:
                _time_to_target = _d_times[_i] / 60
            else:
                _frac = ((_target_pct - _removal_pct[_i-1]) /
                         (_removal_pct[_i] - _removal_pct[_i-1]))
                _time_to_target = (_d_times[_i-1] +
                                   _frac * (_d_times[_i] - _d_times[_i-1])) / 60
            break

    calc = {
        "oxide_name": oxide_dropdown.value,
        "ox": _ox,
        "steel_kg": _steel_kg,
        "cu_init": _cu_init,
        "cu_target": _cu_target,
        "oxide_g": _oxide_g,
        "r_um": _r_um,
        "temp_K": _temp_K,
        "closest_t": _closest_t,
        "phase": _phase,
        "cu_remove_g": _cu_remove_g,
        "oxide_stoich_g": _oxide_stoich_g,
        "excess": _excess,
        "n_particles": _n_particles,
        "area_cm2": _area_cm2,
        "t_diff_s": _t_diff,
        "d_times": _d_times,
        "d_capture": _d_capture,
        "removal_pct": _removal_pct,
        "target_pct": _target_pct,
        "time_to_target": _time_to_target,
        "total_cu_mg": _total_cu_mg,
        "closest_r": _closest_r,
    }
    return (calc,)


# ── Verdict banner + Plot ───────────────────────────────────────────

@app.cell
def _(mo, plt, np, math, calc, DICTRA_DATA, OXIDES, story_toggle, story_frame):
    _c = calc

    # ── Verdict ──────────────────────────────────────────────────────
    if _c["temp_K"] < 1823:
        _verdict = "SOLID STEEL — diffusion ~260x slower"
        _color = "#6b7280"
    elif _c["excess"] >= 1.0 and _c["time_to_target"] is not None:
        if _c["time_to_target"] <= 10:
            _verdict = "FEASIBLE"
            _color = "#22c55e"
        elif _c["time_to_target"] <= 30:
            _verdict = "FEASIBLE (slow)"
            _color = "#eab308"
        else:
            _verdict = "MARGINAL"
            _color = "#f97316"
    elif _c["excess"] < 1.0:
        _verdict = "NEED MORE OXIDE (%.1fg min)" % _c["oxide_stoich_g"]
        _color = "#ef4444"
    else:
        _verdict = "TOO SLOW (> 30 min)"
        _color = "#f97316"

    _tstr = "%.1f min" % _c["time_to_target"] if _c["time_to_target"] else "> 30 min"
    _temp_C = _c["temp_K"] - 273.15

    # Story narrative banner
    _story_html = ""
    if story_toggle.value:
        _narr = story_frame["narrative"]
        if "OPTIMAL" in _narr:
            _story_html = (f'<div style="background:#009988; color:white; '
                          f'padding:10px 16px; border-radius:6px; font-size:1.2em; '
                          f'font-weight:bold; text-align:center; margin-bottom:8px;">'
                          f'{_narr}</div>')
        else:
            _step_color = "#0077BB"
            _story_html = (f'<div style="background:{_step_color}18; '
                          f'border-left:4px solid {_step_color}; '
                          f'padding:8px 16px; border-radius:4px; font-size:1.05em; '
                          f'margin-bottom:8px;">{_narr}</div>')

    _banner = mo.md(f"""{_story_html}<div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap; background:{_color}18; border-left:4px solid {_color}; padding:8px 16px; border-radius:4px;">
<strong style="font-size:1.1em;">{_c["oxide_name"]} -> {_c["ox"]["product"]}</strong>
<span>{_c["temp_K"]}K ({_temp_C:.0f}C) | {_c["phase"]}</span>
<span>dG = {_c["ox"]["dG_1800K_kJ"]:.0f} kJ/mol</span>
<span>Dose: {_c["oxide_g"]:.1f}g ({_c["excess"]:.1f}x stoich)</span>
<span>Time to target: <strong>{_tstr}</strong></span>
<span style="color:{_color}; font-weight:bold;">{_verdict}</span>
</div>""")

    # ── Plot ─────────────────────────────────────────────────────────
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 4.5))

    _tmin = _c["d_times"] / 60
    _ax1.plot(_tmin, _c["removal_pct"],
              color="#0077BB", marker="o", markersize=7, linewidth=2.5,
              label=f'{_c["oxide_name"]} ({_c["oxide_g"]:.0f}g, R={_c["r_um"]}um)',
              zorder=5)
    _ax1.fill_between(_tmin, _c["removal_pct"], alpha=0.1, color="#0077BB")
    _ax1.axhline(_c["target_pct"], color="gray", linestyle="--", alpha=0.6)
    _ax1.text(16, _c["target_pct"] + 2,
              f'Target: {_c["cu_target"]:.2f} wt%',
              fontsize=9, color="gray", style="italic")

    if _c["time_to_target"] is not None and _c["time_to_target"] <= 30:
        _ax1.axvline(_c["time_to_target"], color="#22c55e", linestyle=":",
                     alpha=0.5, linewidth=1.5)
        _ax1.plot(_c["time_to_target"], _c["target_pct"],
                  marker="*", color="#22c55e", markersize=15, zorder=10)

    _ax1.set_xlabel("Contact time (min)", fontsize=11)
    _ax1.set_ylabel("Cu removal (%)", fontsize=11)
    _ax1.set_ylim(0, 105)
    _ax1.set_xlim(0, 32)
    _ax1.set_title("Your Settings", fontsize=12, fontweight="bold")
    _ax1.legend(fontsize=9, loc="lower right")
    _ax1.grid(True, which="major", alpha=0.3)
    _ax1.minorticks_on()
    _ax1.grid(True, which="minor", alpha=0.1)
    for _s in _ax1.spines.values():
        _s.set_visible(False)

    # Right: compare all oxides at same temp/dose/radius
    _ox_colors = {"Fe₂O₃": "#0077BB", "V₂O₅": "#EE7733", "MnO": "#AA3377",
                  "SiO₂": "#009988", "Al₂O₃": "#BBBBBB"}
    _ox_markers = {"Fe₂O₃": "o", "V₂O₅": "s", "MnO": "^",
                   "SiO₂": "D", "Al₂O₃": "v"}

    _mask_rt = ((DICTRA_DATA[:, 0] == _c["closest_t"]) &
                (DICTRA_DATA[:, 1] == _c["closest_r"]))
    _dd_times = DICTRA_DATA[_mask_rt, 2]
    _dd_capture = DICTRA_DATA[_mask_rt, 3]

    for _name, _oxd in OXIDES.items():
        _rm = _c["r_um"] * 1e-6
        _vp = (4/3) * math.pi * _rm**3
        _mp = _oxd["rho"] * _vp * 1000
        _np = _c["oxide_g"] / _mp

        _cu_lim_mol = (_c["oxide_g"] / _oxd["MW_oxide"]) * _oxd["cu_per_mol"]
        _cu_lim_mg = _cu_lim_mol * 63.546 * 1000
        _slimit = min(_cu_lim_mg / _c["total_cu_mg"] * 100, 100)

        _rem = np.minimum(_dd_capture * _np / _c["total_cu_mg"] * 100, _slimit)

        _lw = 2.5 if _name == _c["oxide_name"] else 1.2
        _al = 1.0 if _name == _c["oxide_name"] else 0.5

        _ax2.plot(_dd_times / 60, _rem,
                  color=_ox_colors[_name], marker=_ox_markers[_name],
                  markersize=5, linewidth=_lw, alpha=_al,
                  label=f'{_name} ({_oxd["dG_1800K_kJ"]:.0f} kJ)')

    _ax2.axhline(_c["target_pct"], color="gray", linestyle="--", alpha=0.6)
    _ax2.set_xlabel("Contact time (min)", fontsize=11)
    _ax2.set_ylabel("Cu removal (%)", fontsize=11)
    _ax2.set_ylim(0, 105)
    _ax2.set_xlim(0, 32)
    _ax2.set_title("All 5 Oxides Compared (same dose & radius)", fontsize=12, fontweight="bold")
    _ax2.legend(fontsize=8, loc="lower right")
    _ax2.grid(True, which="major", alpha=0.3)
    _ax2.minorticks_on()
    _ax2.grid(True, which="minor", alpha=0.1)
    for _s in _ax2.spines.values():
        _s.set_visible(False)

    _fig.tight_layout()

    mo.vstack([_banner, _fig])
    return


# ── Details (below the fold) ────────────────────────────────────────

@app.cell
def _(mo, OXIDES, MW_CU, math, calc, D_CU_LIQUID):
    _c = calc

    _tstr2 = "%.1f min" % _c["time_to_target"] if _c["time_to_target"] else "> 30 min"
    _temp_C2 = _c["temp_K"] - 273.15

    _details_md = mo.md(f"""
| | |
|---|---|
| **Reaction** | Cu + {_c["oxide_name"]} + 1/2 O2 -> {_c["ox"]["product"]} |
| **Temperature** | {_c["temp_K"]} K ({_temp_C2:.0f}C) -- {_c["phase"]} |
| **dG (1800K)** | {_c["ox"]["dG_1800K_kJ"]:.1f} kJ/mol ({_c["ox"]["tier"]} tier) |
| **Cu to remove** | {_c["cu_remove_g"]:.2f} g ({_c["cu_init"]:.2f}% -> {_c["cu_target"]:.2f}%) |
| **Stoich oxide** | {_c["oxide_stoich_g"]:.2f} g |
| **Your dose** | {_c["oxide_g"]:.1f} g ({_c["excess"]:.1f}x excess) |
| **Particles** | {_c["n_particles"]:.2e} (R = {_c["r_um"]} um) |
| **Surface area** | {_c["area_cm2"]:.0f} cm2 |
| **Time to target** | {_tstr2} |
    """)

    _rows = []
    for _name, _oxd in OXIDES.items():
        _cu_mol = _c["cu_remove_g"] / MW_CU
        _ox_mol = _cu_mol / _oxd["cu_per_mol"]
        _ox_g = _ox_mol * _oxd["MW_oxide"]
        _exc = _c["oxide_g"] / _ox_g if _ox_g > 0 else 0
        _hl = " **<--**" if _name == _c["oxide_name"] else ""

        _rows.append(
            f"| {_name}{_hl} | {_oxd['product']} | {_oxd['dG_1800K_kJ']:.1f} | "
            f"{_oxd['cu_per_mol']} | {_ox_g:.2f} | {_exc:.1f}x | {_oxd['tier']} |"
        )
    _table = "\n".join(_rows)

    _comparison_md = mo.md(f"""
| Oxide | Product | dG (kJ) | Cu/mol | Stoich (g) | Excess | Tier |
|-------|---------|---------|--------|-----------|--------|------|
{_table}

*Stoich = minimum oxide to capture {_c["cu_remove_g"]:.2f} g Cu.
Excess = your {_c["oxide_g"]:.1f} g dose / stoich.*
    """)

    _rm2 = _c["r_um"] * 1e-6
    _tdiff2 = _rm2**2 / (2 * D_CU_LIQUID)

    _howto_md = mo.md(f"""
**1. Add {_c["oxide_g"]:.0f}g {_c["oxide_name"]} powder (R={_c["r_um"]}um) to {_c["steel_kg"]:.1f}kg steel at {_temp_C2:.0f}C.**
That's {_c["n_particles"]:.2e} particles, {_c["area_cm2"]:.0f} cm2 surface area.

**2. Cu diffuses to nearest particle.** D_Cu = {D_CU_LIQUID:.2e} m2/s (liquid), diffusion time ~ {_tdiff2:.1f}s.
{"**Note: Below liquidus (~1538C), steel is solid and D_Cu drops ~1000x. Diffusion is negligible.**" if _c["temp_K"] < 1823 else ""}

**3. Cu reacts:** Cu + {_c["oxide_name"]} -> {_c["ox"]["product"]} (dG = {_c["ox"]["dG_1800K_kJ"]:.1f} kJ/mol)

**4. Skim slag.** Cu leaves with the oxide. Steel is cleaner.

*Induction furnace stirs electromagnetically -- real removal faster than diffusion-only model.*
    """)

    mo.accordion({
        "Detailed Results": _details_md,
        "Oxide Comparison Table": _comparison_md,
        "How It Works": _howto_md,
    })
    return


# ── Footer ───────────────────────────────────────────────────────────

@app.cell
def _(mo):
    mo.md(r"""
---
*Honda CALPHAD | MSE 4381 Capstone, Spring 2026 | TCOX14 + DICTRA (TCFE13/MOBFE8)*
*Temperature sweep: 1673-1923 K (11 steps) | 220 DICTRA calculations*
    """)
    return


if __name__ == "__main__":
    app.run()
