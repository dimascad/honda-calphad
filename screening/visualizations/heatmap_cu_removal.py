"""
Interactive heatmap of Cu removal across the full DICTRA parameter space.

X-axis: contact time (1, 5, 10, 30 min)
Y-axis: particle radius (25, 50, 100, 250, 500 um)
Color:  system-scale Cu removal (%)
Frames: temperature (1673-1923 K, 11 steps) — play button + scrubber

Outputs: figures/cu_removal_heatmap.html (self-contained, opens in any browser)

Run: python3 screening/heatmap_cu_removal.py
"""

import csv
import math
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "data" / "tcpython" / "raw"
FIG_DIR = SCRIPT_DIR.parent / "figures"
SUMMARY_CSV = RAW_DIR / "cu_removal_rate_summary.csv"

# ── Physical parameters ───────────────────────────────────────────
RHO_OXIDE = 5240       # kg/m3 Fe2O3
CU_INIT_WT = 0.30      # wt%
STEEL_MASS_KG = 0.50   # kg
OXIDE_DOSE_G = 2.0     # grams (shows differentiation; 5g saturates)
MW_CU = 63.546
FE_LIQUIDUS = 1811     # K

TARGET_REMOVAL = (1 - 0.10 / CU_INIT_WT) * 100  # 66.7%


def load_summary():
    rows = []
    with open(SUMMARY_CSV) as f:
        for r in csv.DictReader(f):
            rows.append({
                "temp_K": int(r["temp_K"]),
                "phase": r["phase"],
                "radius_um": int(r["radius_um"]),
                "time_s": int(r["time_s"]),
                "cu_captured_mg": float(r["cu_captured_mg"]),
            })
    return rows


def compute_removal(cu_captured_mg, radius_um):
    r_m = radius_um * 1e-6
    vol = (4 / 3) * math.pi * r_m ** 3
    n = (OXIDE_DOSE_G / 1000) / (RHO_OXIDE * vol)
    total_mg = cu_captured_mg * n
    cu_total_mg = STEEL_MASS_KG * (CU_INIT_WT / 100) * 1e6
    return min(total_mg / cu_total_mg * 100, 100.0)


def main():
    summary = load_summary()

    temps = sorted(set(r["temp_K"] for r in summary))
    radii = sorted(set(r["radius_um"] for r in summary))
    times_s = sorted(set(r["time_s"] for r in summary))

    time_labels = {60: "1 min", 300: "5 min", 600: "10 min", 1800: "30 min"}
    x_labels = [time_labels[t] for t in times_s]
    y_labels = [f"{r} um" for r in radii]

    # Build removal % grid for each temperature
    grids = {}
    for T in temps:
        grid = np.zeros((len(radii), len(times_s)))
        for r in summary:
            if r["temp_K"] == T:
                ri = radii.index(r["radius_um"])
                ti = times_s.index(r["time_s"])
                grid[ri, ti] = compute_removal(r["cu_captured_mg"], r["radius_um"])
        grids[T] = grid

    # Custom text for hover
    def make_hover(T, grid):
        phase = "LIQUID" if T >= 1823 else "FCC_A1 (solid)"
        text = []
        for ri, R in enumerate(radii):
            row = []
            for ti, t in enumerate(times_s):
                val = grid[ri, ti]
                row.append(
                    f"T = {T} K ({phase})<br>"
                    f"R = {R} um<br>"
                    f"t = {time_labels[t]}<br>"
                    f"Removal = {val:.1f}%<br>"
                    f"{'above' if val >= TARGET_REMOVAL else 'below'} target ({TARGET_REMOVAL:.0f}%)"
                )
            text.append(row)
        return text

    # ── Build Plotly figure with animation frames ────────────────
    # Start with first temperature
    T0 = temps[0]
    phase0 = "SOLID" if T0 < 1823 else "LIQUID"

    fig = go.Figure(
        data=[go.Heatmap(
            z=grids[T0],
            x=x_labels,
            y=y_labels,
            colorscale=[
                [0.0, "#f7fbff"],     # near-white for 0%
                [0.15, "#c6dbef"],    # light blue
                [0.35, "#6baed6"],    # medium blue
                [0.50, "#2171b5"],    # blue
                [0.667, "#AA3377"],   # purple at target (66.7%)
                [0.80, "#EE7733"],    # orange
                [1.0, "#009988"],     # teal for 100%
            ],
            zmin=0,
            zmax=100,
            text=make_hover(T0, grids[T0]),
            hoverinfo="text",
            colorbar=dict(
                title="Cu Removal (%)",
                tickvals=[0, 25, 50, TARGET_REMOVAL, 75, 100],
                ticktext=["0%", "25%", "50%", f"Target ({TARGET_REMOVAL:.0f}%)", "75%", "100%"],
            ),
            # Show values on cells
            texttemplate="%{z:.1f}%",
            textfont=dict(size=11),
        )],
        layout=go.Layout(
            title=dict(
                text=(f"Cu Removal Heatmap — {OXIDE_DOSE_G:.0f}g Fe₂O₃ in "
                      f"{STEEL_MASS_KG} kg steel ({CU_INIT_WT}% Cu)<br>"
                      f"<span style='font-size:14px; color:#888;'>"
                      f"T = {T0} K ({phase0}) — Use play button or slider below</span>"),
                font=dict(size=18),
            ),
            xaxis=dict(title="Contact Time", side="bottom"),
            yaxis=dict(title="Particle Radius", autorange=True),
            width=800,
            height=550,
            # Animation controls
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                y=0,
                x=0.5,
                xanchor="center",
                yanchor="top",
                pad=dict(t=60, b=10),
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[None, dict(
                            frame=dict(duration=800, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=300),
                        )],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode="immediate",
                            transition=dict(duration=0),
                        )],
                    ),
                ],
            )],
            # Temperature slider
            sliders=[dict(
                active=0,
                yanchor="top",
                xanchor="left",
                currentvalue=dict(
                    prefix="Temperature: ",
                    suffix=" K",
                    visible=True,
                    xanchor="center",
                    font=dict(size=14),
                ),
                transition=dict(duration=300),
                pad=dict(b=10, t=30),
                len=0.9,
                x=0.05,
                y=0,
                steps=[
                    dict(
                        args=[[f"T_{T}"], dict(
                            frame=dict(duration=300, redraw=True),
                            mode="immediate",
                            transition=dict(duration=300),
                        )],
                        label=f"{T}",
                        method="animate",
                    )
                    for T in temps
                ],
            )],
            margin=dict(b=120),
        ),
        frames=[
            go.Frame(
                data=[go.Heatmap(
                    z=grids[T],
                    x=x_labels,
                    y=y_labels,
                    colorscale=[
                        [0.0, "#f7fbff"],
                        [0.15, "#c6dbef"],
                        [0.35, "#6baed6"],
                        [0.50, "#2171b5"],
                        [0.667, "#AA3377"],
                        [0.80, "#EE7733"],
                        [1.0, "#009988"],
                    ],
                    zmin=0,
                    zmax=100,
                    text=make_hover(T, grids[T]),
                    hoverinfo="text",
                    texttemplate="%{z:.1f}%",
                    textfont=dict(size=11),
                )],
                name=f"T_{T}",
                layout=go.Layout(
                    title=dict(
                        text=(f"Cu Removal Heatmap — {OXIDE_DOSE_G:.0f}g Fe₂O₃ in "
                              f"{STEEL_MASS_KG} kg steel ({CU_INIT_WT}% Cu)<br>"
                              f"<span style='font-size:14px; color:"
                              f"{'#009988' if T >= 1823 else '#CC3311'};'>"
                              f"T = {T} K ({'LIQUID' if T >= 1823 else 'SOLID'})"
                              f"{' — Fe liquidus crossed!' if T == 1823 else ''}"
                              f"</span>"),
                    ),
                ),
            )
            for T in temps
        ],
    )

    out_html = FIG_DIR / "cu_removal_heatmap.html"
    fig.write_html(str(out_html), include_plotlyjs=True, full_html=True)
    print(f"Saved: {out_html} ({out_html.stat().st_size / 1024:.0f} KB)")
    print("Opening in browser...")


if __name__ == "__main__":
    main()
