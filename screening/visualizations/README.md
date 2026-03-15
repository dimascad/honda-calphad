# Cu Removal Visualizations

Scripts and outputs for interactive/animated DICTRA Cu removal data.

## Completed Visualizations

| Script | Output | Type | Description |
|--------|--------|------|-------------|
| `animate_cu_removal.py` | `figures/cu_removal_sweep.gif` | GIF | Parameter sweep animation (T→R→dose→optimal). Gauge-style dashboard. |
| `heatmap_cu_removal.py` | `figures/cu_removal_heatmap.html` | Plotly HTML | 2D heatmap (radius × time), temperature as animation frames. |
| `surface3d_cu_removal.py` | `figures/cu_removal_3d.html` | Plotly HTML | 3D surface (radius × time × removal%), animated over temperature. Gray=solid reference, purple plane=target. |
| `plotly_cu_removal.py` | `figures/cu_removal_interactive.html` | Plotly HTML | Animated line chart: 5 radius curves morphing as temperature sweeps. Play button + scrubber. |
| `dose_response_curves.py` | `figures/dose_response_curves.png/pdf` | Static (2-panel) | Dose-response: removal % vs oxide mass for all 5 oxides. Left=30min (stoich-limited), right=1min (kinetics-limited). Crossover doses annotated. |
| `sensitivity_tornado.py` | `figures/sensitivity_tornado.png/pdf` | Static | Tornado chart: one-at-a-time perturbations showing particle radius is the #1 lever (76.6 pp swing). |
| `breakeven_contour.py` | `figures/breakeven_contour.png/pdf` | Static | 2D contour (dose × radius) with 66.7% target contour for all 5 oxides. Shows feasible operating window and stoich/kinetics regime boundary. |
| `oxide_decision_matrix.py` | `figures/oxide_decision_matrix.png/pdf` | Static | Radar chart: 5 oxides × 5 criteria. SiO₂ dominates efficiency, Fe₂O₃/V₂O₅ dominate thermodynamics. No single winner. |
| `thermo_kinetics_overlay.py` | `figures/thermo_kinetics_overlay.png/pdf` | Static | Scatter: |ΔG| vs removal % with time evolution (4 markers per oxide). Thermo and kinetics are anti-correlated. |
| `experiment_predictor.py` | `figures/experiment_predictor.png/pdf` | Static (5-panel) | Heatmap "recipe card": predicted final Cu wt% for each oxide × dose × particle size. Green = meets 0.10% target. |
| `../plot_cu_removal_rate.py` | `figures/cu_removal_*.png/pdf` | Static (4 figs) | Publication-quality DICTRA plots: profiles, per-particle capture, system-scale removal, temperature effect. |

## Marimo Interactive Notebook

| File | URL | Description |
|------|-----|-------------|
| `simulations/notebooks/cu_removal_interactive.py` | [molab](https://molab.marimo.io/notebooks/nb_dRsVuCmRdf5F8LjdcZppjq/app) | Full experiment designer with sliders (T, R, dose, oxide, Cu%). Story Mode auto-cycles through optimization sequence with moving sliders. |

## Planned Visualizations (TODO)

Priority order — build one at a time:

1. ~~**Dose-Response Curves**~~ DONE — `dose_response_curves.py`

   **Minimum dose for 66.7% Cu removal (0.30 → 0.10 wt%) in 0.5 kg steel at 1823 K, R=100 μm:**

   | Oxide | 30-min dose | 1-min dose | Ratio |
   |-------|------------|-----------|-------|
   | SiO₂  | 0.47 g | 3.53 g | 7.5x |
   | V₂O₅  | 0.95 g | 4.47 g | 4.7x |
   | Al₂O₃ | 1.61 g | 5.26 g | 3.3x |
   | MnO   | 2.23 g | 7.23 g | 3.2x |
   | Fe₂O₃ | 2.51 g | 6.97 g | 2.8x |

   The "ratio" column shows how much more oxide you'd need with only 1 min of contact vs 30 min — a direct measure of how much kinetics matters for each oxide. SiO₂ is most sensitive because its stoichiometric efficiency is so high that even small kinetic shortfalls require big dose increases.

   At 30 min, stoichiometry is the bottleneck: the oxide's molar Cu capacity (`cu_per_mol / MW`) determines the slope. At 1 min, kinetics dominates — per-particle capture drops 20x (0.062 → 0.003 mg) and the curves compress because Cu diffusion is oxide-independent.

2. ~~**Sensitivity Tornado**~~ DONE — `sensitivity_tornado.py`

   **Baseline:** T=1823K, R=250μm, t=10min, dose=3g Fe₂O₃ → 16.4% removal.

   | Parameter | Low | Low % | High | High % | Swing |
   |-----------|-----|-------|------|--------|-------|
   | Particle radius | 500 μm | 3.0% | 50 μm | 79.6% | 76.6 pp |
   | Oxide dose | 1 g | 5.5% | 10 g | 54.5% | 49.1 pp |
   | Contact time | 1 min | 3.4% | 30 min | 42.0% | 38.6 pp |
   | Temperature | 1773 K (solid) | 0.6% | 1873 K | 17.5% | 17.0 pp |
   | Oxide choice | MnO | 15.8% | SiO₂ | 32.3% | 16.6 pp |

   **Key takeaways:**
   - **Particle radius is the #1 lever** (76.6 pp swing). Going from 250→50 μm means 125x more particles per gram (radius cubed). This is the single most impactful thing to control in the Fontana Lab experiment — use the finest oxide powder available.
   - **Temperature is an asymmetric risk, not an opportunity.** The downside is catastrophic (16.4% → 0.6% below liquidus) but the upside is negligible (16.4% → 17.5% at +50K). Ensure you're above the liquidus, but don't waste energy going much hotter.
   - **Oxide choice is the smallest bar** — all 5 candidates are within ~16 pp of each other. The thermodynamic ranking (dG) matters for whether the reaction *proceeds*, but for kinetic removal the differences are modest. Pick the oxide based on dG and practicality, not kinetic efficiency.
3. ~~**Break-Even Contour Map**~~ DONE — `breakeven_contour.py`

   Filled contour of Cu removal % over (dose × radius) for Fe₂O₃, with the 66.7% target contour overlaid for all 5 oxides. Below-right of each line is the feasible window.

   **Key takeaways:**
   - **Two distinct regimes visible.** Below ~200 μm radius, contour lines are nearly vertical (stoichiometry-limited — just add more grams). Above ~200 μm, they curve sharply upward (kinetics-limited — even 20g of oxide isn't enough with coarse particles).
   - **SiO₂ has the widest feasible window** (teal dotted line, highest contour) — it can tolerate the coarsest particles at any given dose because of its high stoichiometric efficiency (2 Cu/mol at only 60 g/mol).
   - **Fe₂O₃ and MnO have the tightest windows** — they need finer particles or more mass to reach the same removal. Fe₂O₃ is kinetics-limited at large R (dense particles, fewer per gram), MnO is stoich-limited (only 0.5 Cu/mol).
   - **Practical reading:** pick your powder size on the y-axis, read across to the contour line for your oxide, and read down to get the minimum dose needed.
4. ~~**Oxide Decision Matrix**~~ DONE — `oxide_decision_matrix.py`

   Radar chart comparing 5 oxides on 5 criteria (|ΔG|, Cu capacity per gram, particle count via 1/density, melting point, dose efficiency via 1/min_dose). All axes oriented so bigger polygon = better.

   **Key takeaways:**
   - **SiO₂ dominates 3 of 5 axes** (Cu capacity, particle count, dose efficiency) — its polygon is the largest. It captures 2 Cu per mol at only 60 g/mol, giving the highest stoichiometric efficiency by far.
   - **Fe₂O₃ and V₂O₅ dominate thermodynamics** (|ΔG|) — strongest driving force for the reaction to proceed. But they're mediocre on efficiency.
   - **Al₂O₃ wins only on melting point** (2072°C) — it stays solid longest at steelmaking temps, which matters for particle integrity. But weakest ΔG of the group.
   - **No single oxide wins all axes** — the tradeoff is thermodynamic driving force (Fe₂O₃/V₂O₅) vs mass efficiency (SiO₂). This is the core experiment design decision.
5. ~~**Thermo × Kinetics Overlay**~~ DONE — `thermo_kinetics_overlay.py`

   Scatter of |ΔG| (x) vs removal % (y) at R=250μm, dose=3g, T=1823K. Each oxide shows 4 connected markers (1→30 min, growing in size). Ideal = top-right corner.

   **Key takeaways:**
   - **Thermodynamics and kinetics are anti-correlated.** Fe₂O₃ has the strongest ΔG (111.9 kJ) but only 42% removal at 30 min. SiO₂ has the weakest strong-tier ΔG (50.2 kJ) but the highest removal (83%). No oxide sits in the ideal top-right corner.
   - **V₂O₅ is the closest to the ideal corner** — strong ΔG (109.2 kJ) and 65.5% removal at 30 min (just shy of the 66.7% target). It's the best compromise between the two axes.
   - **Time helps everyone roughly equally** — all 5 oxides' vertical lines span a similar range. The spread in removal comes from density and stoichiometric capacity, not kinetic rate (since Cu diffusion is oxide-independent).
   - **At these conditions (R=250, dose=3g), only SiO₂ crosses the 66.7% target.** V₂O₅ nearly makes it. The others need more dose or finer particles.

   **Open questions (revisit with Zhang):**
   - **Why 66.7%?** It's 0.30→0.10 wt% Cu (hot shortness threshold). Confirm this target with Honda — they may want lower.
   - **Two valid rankings exist:** thermodynamic (Fe₂O₃ > V₂O₅ > MnO > SiO₂ > Al₂O₃) vs mass efficiency (SiO₂ > V₂O₅ > Al₂O₃ > MnO > Fe₂O₃). They give opposite answers. Which matters more for experiment design?
   - **SiO₂ (sand/quartz) is a serious candidate.** MP=1713°C (solid at steelmaking temps), cheapest oxide, highest Cu capacity per gram. But weakest ΔG (-50.2 kJ) of the strong tier. Is -50 kJ enough driving force? Cu₂SiO₄ dissolves into ionic liquid slag at 1800K — does the Cu stay captured in the slag, or does it re-equilibrate back into the steel?
   - **Does ΔG ranking = experiment ranking?** If all 5 reactions are thermodynamically favorable (all ΔG < 0), then maybe the kinetic/efficiency ranking is what actually determines how much Cu gets removed in practice. The ΔG just needs to be "negative enough" — exact magnitude may not matter much above a threshold.
6. ~~**Experimental Outcome Predictor**~~ DONE — `experiment_predictor.py`

   5-panel heatmap: one panel per oxide, rows = particle radius (50, 100, 250, 500 μm), columns = oxide dose (1, 2, 3, 5, 10 g). Each cell shows predicted final Cu wt% after 30 min at 1823K in 0.5 kg steel starting at 0.30 wt% Cu. Green cells meet the 0.10 wt% target.

   **Feasible combinations (out of 20 per oxide):**

   | Oxide | Feasible | Best combo |
   |-------|----------|------------|
   | SiO₂  | 13/20 | R=50μm, dose=1g |
   | V₂O₅  | 12/20 | R=50μm, dose=1g |
   | Al₂O₃ | 10/20 | R=50μm, dose=2g |
   | Fe₂O₃ |  8/20 | R=50μm, dose=3g |
   | MnO   |  8/20 | R=50μm, dose=3g |

   **Key takeaways:**
   - **SiO₂ is the most forgiving oxide** — works even at 250 μm with 5g dose. Fe₂O₃ and MnO require fine particles (≤100 μm) or heavy doses (≥5g).
   - **Particle radius is the dominant variable** (consistent with tornado chart). At 500 μm, only SiO₂ and V₂O₅ can reach the target, and only at 10g dose.
   - **This is the "recipe card" for experiment planning.** Pick your oxide, read across to find which dose + particle size combinations are predicted to succeed.
   - All predictions use DICTRA per-particle Cu capture (real kinetic data) with stoichiometric capping. No empirical fudge factors.

## Data Source

All visualizations use `data/tcpython/raw/cu_removal_rate_summary.csv` (220 rows: 11 temps × 5 radii × 4 times) from the DICTRA temperature sweep (March 15, 2026). Physical parameters: Fe2O3 (rho=5240 kg/m3), 0.5 kg steel, 0.30 wt% Cu initial.

## Running

```bash
# Static plots (4 figures)
python3 screening/plot_cu_removal_rate.py

# Interactive visualizations
python3 screening/visualizations/plotly_cu_removal.py
python3 screening/visualizations/heatmap_cu_removal.py
python3 screening/visualizations/surface3d_cu_removal.py
python3 screening/visualizations/animate_cu_removal.py
python3 screening/visualizations/dose_response_curves.py
python3 screening/visualizations/sensitivity_tornado.py
python3 screening/visualizations/breakeven_contour.py
python3 screening/visualizations/oxide_decision_matrix.py
python3 screening/visualizations/thermo_kinetics_overlay.py
python3 screening/visualizations/experiment_predictor.py

# Marimo notebook
python3 -m marimo edit simulations/notebooks/cu_removal_interactive.py --port 2718 --no-token
```
