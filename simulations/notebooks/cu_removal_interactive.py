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

    DICTRA_DATA = np.array([
        [25,   60,  0.00216], [25,  300,  0.00974],
        [25,  600,  0.01902], [25, 1800,  0.05575],
        [50,   60,  0.00242], [50,  300,  0.01027],
        [50,  600,  0.01975], [50, 1800,  0.05707],
        [100,  60,  0.00305], [100, 300,  0.01146],
        [100, 600,  0.02134], [100,1800,  0.05984],
        [250,  60,  0.00573], [250, 300,  0.01597],
        [250, 600,  0.02715], [250,1800,  0.06935],
        [500,  60,  0.01279], [500, 300,  0.02664],
        [500, 600,  0.04023], [500,1800,  0.08911],
    ])

    return D_CU_LIQUID, DICTRA_DATA, MW_CU, OXIDES


# ── UI Controls ──────────────────────────────────────────────────────

@app.cell
def _(mo, OXIDES):
    oxide_dropdown = mo.ui.dropdown(
        options=list(OXIDES.keys()),
        value="Fe₂O₃",
        label="Oxide"
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
        start=0.5, stop=20.0, step=0.5, value=5.0,
        label="Oxide dose (g)"
    )
    particle_radius_slider = mo.ui.slider(
        start=25, stop=500, step=25, value=100,
        label="Particle R (um)"
    )

    mo.hstack([
        mo.vstack([
            mo.md("# Cu Removal — Experiment Designer"),
            mo.hstack([oxide_dropdown, steel_mass_slider, cu_init_slider], justify="start", gap=0.5),
            mo.hstack([cu_target_slider, oxide_mass_slider, particle_radius_slider], justify="start", gap=0.5),
        ]),
    ])
    return (
        cu_init_slider, cu_target_slider, oxide_dropdown,
        oxide_mass_slider, particle_radius_slider, steel_mass_slider,
    )


# ── Core calculation (no output) ────────────────────────────────────

@app.cell
def _(
    math, np, MW_CU, OXIDES, DICTRA_DATA,
    oxide_dropdown, steel_mass_slider, cu_init_slider,
    cu_target_slider, oxide_mass_slider, particle_radius_slider,
):
    _ox = OXIDES[oxide_dropdown.value]
    _steel_kg = steel_mass_slider.value
    _cu_init = cu_init_slider.value
    _cu_target = cu_target_slider.value
    _oxide_g = oxide_mass_slider.value
    _r_um = particle_radius_slider.value

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

    _avail_r = sorted(set(DICTRA_DATA[:, 0].astype(int)))
    _closest = min(_avail_r, key=lambda x: abs(x - _r_um))
    _mask = DICTRA_DATA[:, 0] == _closest
    _d_times = DICTRA_DATA[_mask, 1]
    _d_capture = DICTRA_DATA[_mask, 2]

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
        "closest_r": _closest,
    }
    return (calc,)


# ── Verdict banner (compact) + Plot ─────────────────────────────────

@app.cell
def _(mo, plt, np, math, calc, DICTRA_DATA, OXIDES):
    _c = calc

    # ── Verdict ──────────────────────────────────────────────────────
    if _c["excess"] >= 1.0 and _c["time_to_target"] is not None:
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

    _banner = mo.md(f"""<div style="display:flex; align-items:center; gap:24px; background:{_color}18; border-left:4px solid {_color}; padding:8px 16px; border-radius:4px;">
<strong style="font-size:1.1em;">{_c["oxide_name"]} → {_c["ox"]["product"]}</strong>
<span>dG = {_c["ox"]["dG_1800K_kJ"]:.0f} kJ/mol</span>
<span>Dose: {_c["oxide_g"]:.1f}g ({_c["excess"]:.1f}x stoich)</span>
<span>Time to target: <strong>{_tstr}</strong></span>
<span style="color:{_color}; font-weight:bold;">{_verdict}</span>
</div>""")

    # ── Plot ─────────────────────────────────────────────────────────
    _fig, (_ax1, _ax2) = plt.subplots(1, 2, figsize=(14, 4.5))

    # Left: current settings
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

    # Right: compare all oxides
    _ox_colors = {"Fe₂O₃": "#0077BB", "V₂O₅": "#EE7733", "MnO": "#AA3377",
                  "SiO₂": "#009988", "Al₂O₃": "#BBBBBB"}
    _ox_markers = {"Fe₂O₃": "o", "V₂O₅": "s", "MnO": "^",
                   "SiO₂": "D", "Al₂O₃": "v"}

    _mask_r = DICTRA_DATA[:, 0] == _c["closest_r"]
    _dd_times = DICTRA_DATA[_mask_r, 1]
    _dd_capture = DICTRA_DATA[_mask_r, 2]

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

    # Combine verdict + plot into one output
    mo.vstack([_banner, _fig])
    return


# ── Details (below the fold) ────────────────────────────────────────

@app.cell
def _(mo, OXIDES, MW_CU, math, calc, D_CU_LIQUID):
    _c = calc

    # ── Results table ────────────────────────────────────────────────
    _tstr2 = "%.1f min" % _c["time_to_target"] if _c["time_to_target"] else "> 30 min"

    _details_md = mo.md(f"""
| | |
|---|---|
| **Reaction** | Cu + {_c["oxide_name"]} + 1/2 O₂ → {_c["ox"]["product"]} |
| **dG (1800K)** | {_c["ox"]["dG_1800K_kJ"]:.1f} kJ/mol ({_c["ox"]["tier"]} tier) |
| **Cu to remove** | {_c["cu_remove_g"]:.2f} g ({_c["cu_init"]:.2f}% → {_c["cu_target"]:.2f}%) |
| **Stoich oxide** | {_c["oxide_stoich_g"]:.2f} g |
| **Your dose** | {_c["oxide_g"]:.1f} g ({_c["excess"]:.1f}x excess) |
| **Particles** | {_c["n_particles"]:.2e} (R = {_c["r_um"]} um) |
| **Surface area** | {_c["area_cm2"]:.0f} cm² |
| **Time to target** | {_tstr2} |
    """)

    # ── Comparison table ─────────────────────────────────────────────
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

    # ── How it works ─────────────────────────────────────────────────
    _rm2 = _c["r_um"] * 1e-6
    _tdiff2 = _rm2**2 / (2 * D_CU_LIQUID)

    _howto_md = mo.md(f"""
**1. Add {_c["oxide_g"]:.0f}g {_c["oxide_name"]} powder (R={_c["r_um"]}um) to {_c["steel_kg"]:.1f}kg steel at 1527°C.**
That's {_c["n_particles"]:.2e} particles, {_c["area_cm2"]:.0f} cm² surface area.

**2. Cu diffuses to nearest particle.** D_Cu = {D_CU_LIQUID:.2e} m²/s, diffusion time ~ {_tdiff2:.1f}s.

**3. Cu reacts:** Cu + {_c["oxide_name"]} → {_c["ox"]["product"]} (dG = {_c["ox"]["dG_1800K_kJ"]:.1f} kJ/mol)

**4. Skim slag.** Cu leaves with the oxide. Steel is cleaner.

*Induction furnace stirs electromagnetically — real removal faster than diffusion-only model.*
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
    """)
    return


if __name__ == "__main__":
    app.run()
