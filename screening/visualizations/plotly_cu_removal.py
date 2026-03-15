"""
Interactive Plotly line chart: Cu removal % vs contact time.

Five curves (one per particle radius) animate as temperature sweeps
from 1673→1923 K. Play button, temperature scrubber, hover tooltips.

At solid temps the curves are flat near zero. Cross the liquidus and
they leap up — you watch the data morph in real time.

Outputs: figures/cu_removal_interactive.html
Run: python3 screening/plotly_cu_removal.py
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
RHO_OXIDE = 5240
CU_INIT_WT = 0.30
STEEL_MASS_KG = 0.50
OXIDE_DOSE_G = 5.0

TARGET_REMOVAL = (1 - 0.10 / CU_INIT_WT) * 100  # 66.7%

# Colorblind palette
COLORS = {
    25:  "#0077BB",  # blue
    50:  "#EE7733",  # orange
    100: "#AA3377",  # purple
    250: "#009988",  # teal
    500: "#CC3311",  # red
}
DASH = {
    25: "solid", 50: "dash", 100: "dot", 250: "dashdot", 500: "longdash",
}


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
    times_min = [t / 60 for t in times_s]

    # Precompute all curves: {(T, R): [removal_pct for each time]}
    curves = {}
    for T in temps:
        for R in radii:
            vals = []
            for t in times_s:
                match = [r for r in summary
                         if r["temp_K"] == T and r["radius_um"] == R
                         and r["time_s"] == t]
                if match:
                    vals.append(compute_removal(match[0]["cu_captured_mg"], R))
                else:
                    vals.append(0.0)
            curves[(T, R)] = vals

    # ── Build figure ─────────────────────────────────────────────
    T0 = temps[0]

    fig = go.Figure()

    # One trace per radius (initial frame)
    for R in radii:
        fig.add_trace(go.Scatter(
            x=times_min,
            y=curves[(T0, R)],
            mode="lines+markers",
            name=f"R = {R} um",
            line=dict(color=COLORS[R], width=3, dash=DASH[R]),
            marker=dict(size=8),
            hovertemplate=(
                f"R = {R} um<br>"
                "t = %{x:.0f} min<br>"
                "Removal = %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    # Target line
    fig.add_trace(go.Scatter(
        x=[0, 35],
        y=[TARGET_REMOVAL, TARGET_REMOVAL],
        mode="lines",
        name=f"Target ({TARGET_REMOVAL:.0f}%)",
        line=dict(color="#AA3377", width=2, dash="dash"),
        hoverinfo="skip",
    ))

    # ── Animation frames ─────────────────────────────────────────
    frames = []
    for T in temps:
        phase = "LIQUID" if T >= 1823 else "SOLID"
        phase_color = "#009988" if T >= 1823 else "#CC3311"

        frame_traces = []
        for R in radii:
            frame_traces.append(go.Scatter(
                x=times_min,
                y=curves[(T, R)],
                mode="lines+markers",
                name=f"R = {R} um",
                line=dict(color=COLORS[R], width=3, dash=DASH[R]),
                marker=dict(size=8),
                hovertemplate=(
                    f"R = {R} um<br>"
                    "t = %{x:.0f} min<br>"
                    "Removal = %{y:.1f}%<br>"
                    f"T = {T} K ({phase})"
                    "<extra></extra>"
                ),
            ))
        # Target line (unchanged)
        frame_traces.append(go.Scatter(
            x=[0, 35],
            y=[TARGET_REMOVAL, TARGET_REMOVAL],
            mode="lines",
            line=dict(color="#AA3377", width=2, dash="dash"),
            hoverinfo="skip",
        ))

        # Find max removal at 30 min for annotation
        max_removal = max(curves[(T, R)][-1] for R in radii)
        best_R = max(radii, key=lambda R: curves[(T, R)][-1])

        frames.append(go.Frame(
            data=frame_traces,
            name=f"T_{T}",
            layout=go.Layout(
                title=dict(
                    text=(f"<b>Cu Removal vs Contact Time</b> — "
                          f"{OXIDE_DOSE_G:.0f}g Fe₂O₃, {STEEL_MASS_KG} kg steel"
                          f"<br><span style='font-size:14px; color:{phase_color};'>"
                          f"T = {T} K ({phase})"
                          f"{'  ⚡ LIQUIDUS CROSSED — curves jump ~260x' if T == 1823 else ''}"
                          f"</span>"
                          f"<br><span style='font-size:12px; color:#888;'>"
                          f"Best: R={best_R} um at 30 min → {max_removal:.1f}% removal"
                          f"</span>"),
                ),
                annotations=[
                    dict(
                        x=30, y=max_removal,
                        text=f"{max_removal:.0f}%",
                        showarrow=True, arrowhead=2,
                        ax=30, ay=-30,
                        font=dict(size=13, color=COLORS[best_R]),
                    ),
                ] if max_removal > 1 else [],
            ),
        ))

    fig.frames = frames

    # ── Layout ───────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(f"<b>Cu Removal vs Contact Time</b> — "
                  f"{OXIDE_DOSE_G:.0f}g Fe₂O₃, {STEEL_MASS_KG} kg steel"
                  f"<br><span style='font-size:14px; color:#888;'>"
                  f"Use play button or temperature slider below</span>"),
            font=dict(size=16),
        ),
        xaxis=dict(
            title="Contact Time (min)",
            range=[0, 33],
            tickvals=times_min,
            gridcolor="#E0E0E0",
        ),
        yaxis=dict(
            title="Cu Removal (%)",
            range=[0, 105],
            gridcolor="#E0E0E0",
        ),
        legend=dict(
            x=0.02, y=0.98,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#CCC",
            borderwidth=1,
        ),
        plot_bgcolor="white",
        width=900,
        height=600,
        # Play/pause
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=-0.08,
            x=0.5,
            xanchor="center",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=800, redraw=True),
                        fromcurrent=True,
                        transition=dict(duration=400, easing="cubic-in-out"),
                    )],
                ),
                dict(
                    label="⏸ Pause",
                    method="animate",
                    args=[[None], dict(
                        frame=dict(duration=0, redraw=False),
                        mode="immediate",
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
            transition=dict(duration=400, easing="cubic-in-out"),
            pad=dict(b=10, t=40),
            len=0.9,
            x=0.05,
            y=-0.05,
            steps=[
                dict(
                    args=[[f"T_{T}"], dict(
                        frame=dict(duration=400, redraw=True),
                        mode="immediate",
                        transition=dict(duration=400),
                    )],
                    label=f"{T}",
                    method="animate",
                )
                for T in temps
            ],
        )],
        margin=dict(b=130),
    )

    out_html = FIG_DIR / "cu_removal_interactive.html"
    fig.write_html(str(out_html), include_plotlyjs=True, full_html=True)
    print(f"Saved: {out_html} ({out_html.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
