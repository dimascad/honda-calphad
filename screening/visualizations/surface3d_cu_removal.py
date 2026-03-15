"""
Interactive 3D surface of Cu removal across the DICTRA parameter space.

Axes:
  X: contact time (1, 5, 10, 30 min)
  Y: particle radius (25-500 um)
  Z: Cu removal (%)

Two surfaces shown simultaneously:
  - Solid steel (1798 K, FCC_A1) — flat, near-zero surface
  - Liquid steel (1923 K, LIQUID) — dramatically higher surface

Plus a transparent plane at the target removal threshold (66.7%).
Rotate, zoom, hover for exact values.

Temperature animation frames also available via play button.

Outputs: figures/cu_removal_3d.html
Run: python3 screening/surface3d_cu_removal.py
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
OXIDE_DOSE_G = 5.0  # 5g shows more interesting surface shape
FE_LIQUIDUS = 1811

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


def build_grid(summary, T, radii, times_s):
    """Build 2D removal % grid for one temperature."""
    grid = np.zeros((len(radii), len(times_s)))
    for r in summary:
        if r["temp_K"] == T:
            ri = radii.index(r["radius_um"])
            ti = times_s.index(r["time_s"])
            grid[ri, ti] = compute_removal(r["cu_captured_mg"], r["radius_um"])
    return grid


def main():
    summary = load_summary()

    temps = sorted(set(r["temp_K"] for r in summary))
    radii = sorted(set(r["radius_um"] for r in summary))
    times_s = sorted(set(r["time_s"] for r in summary))
    times_min = [t / 60 for t in times_s]

    # Meshgrid for surface
    T_mesh, R_mesh = np.meshgrid(times_min, radii)

    # Build grids for all temperatures
    grids = {T: build_grid(summary, T, radii, times_s) for T in temps}

    # Target plane
    target_z = np.full_like(T_mesh, TARGET_REMOVAL, dtype=float)

    # ── Build figure with animation ──────────────────────────────

    # Initial frame: show 1798K (solid) and 1923K (liquid) together
    T_solid = 1798
    T_liquid = 1923

    fig = go.Figure()

    # Solid surface (always shown, semi-transparent)
    fig.add_trace(go.Surface(
        x=T_mesh, y=R_mesh, z=grids[T_solid],
        colorscale=[[0, "#CCCCCC"], [1, "#888888"]],
        opacity=0.4,
        showscale=False,
        name=f"Solid ({T_solid} K)",
        hovertemplate=(
            "Time: %{x:.0f} min<br>"
            "Radius: %{y:.0f} um<br>"
            "Removal: %{z:.1f}%<br>"
            f"T = {T_solid} K (SOLID)"
            "<extra></extra>"
        ),
    ))

    # Animated liquid surface
    fig.add_trace(go.Surface(
        x=T_mesh, y=R_mesh, z=grids[temps[0]],
        colorscale=[
            [0.0, "#f7fbff"],
            [0.2, "#6baed6"],
            [0.5, "#2171b5"],
            [0.667, "#AA3377"],
            [0.85, "#EE7733"],
            [1.0, "#009988"],
        ],
        cmin=0, cmax=100,
        opacity=0.85,
        name=f"T = {temps[0]} K",
        colorbar=dict(
            title="Cu Removal (%)",
            tickvals=[0, 25, 50, TARGET_REMOVAL, 75, 100],
            ticktext=["0%", "25%", "50%", f"Target", "75%", "100%"],
            x=1.02,
        ),
        hovertemplate=(
            "Time: %{x:.0f} min<br>"
            "Radius: %{y:.0f} um<br>"
            "Removal: %{z:.1f}%<br>"
            "<extra></extra>"
        ),
    ))

    # Target plane
    fig.add_trace(go.Surface(
        x=T_mesh, y=R_mesh, z=target_z,
        colorscale=[[0, "#AA3377"], [1, "#AA3377"]],
        opacity=0.15,
        showscale=False,
        name=f"Target ({TARGET_REMOVAL:.0f}%)",
        hoverinfo="skip",
    ))

    # ── Animation frames ─────────────────────────────────────────
    frames = []
    for T in temps:
        phase = "LIQUID" if T >= 1823 else "SOLID"
        phase_color = "#009988" if T >= 1823 else "#CC3311"
        frames.append(go.Frame(
            data=[
                # Solid reference (unchanged)
                go.Surface(
                    x=T_mesh, y=R_mesh, z=grids[T_solid],
                    colorscale=[[0, "#CCCCCC"], [1, "#888888"]],
                    opacity=0.4,
                    showscale=False,
                    hovertemplate=(
                        "Time: %{x:.0f} min<br>"
                        "Radius: %{y:.0f} um<br>"
                        "Removal: %{z:.1f}%<br>"
                        f"T = {T_solid} K (SOLID reference)"
                        "<extra></extra>"
                    ),
                ),
                # Current temperature surface
                go.Surface(
                    x=T_mesh, y=R_mesh, z=grids[T],
                    colorscale=[
                        [0.0, "#f7fbff"],
                        [0.2, "#6baed6"],
                        [0.5, "#2171b5"],
                        [0.667, "#AA3377"],
                        [0.85, "#EE7733"],
                        [1.0, "#009988"],
                    ],
                    cmin=0, cmax=100,
                    opacity=0.85,
                    colorbar=dict(
                        title="Cu Removal (%)",
                        tickvals=[0, 25, 50, TARGET_REMOVAL, 75, 100],
                        ticktext=["0%", "25%", "50%", f"Target", "75%", "100%"],
                        x=1.02,
                    ),
                    hovertemplate=(
                        "Time: %{x:.0f} min<br>"
                        "Radius: %{y:.0f} um<br>"
                        "Removal: %{z:.1f}%<br>"
                        f"T = {T} K ({phase})"
                        "<extra></extra>"
                    ),
                ),
                # Target plane (unchanged)
                go.Surface(
                    x=T_mesh, y=R_mesh, z=target_z,
                    colorscale=[[0, "#AA3377"], [1, "#AA3377"]],
                    opacity=0.15,
                    showscale=False,
                    hoverinfo="skip",
                ),
            ],
            name=f"T_{T}",
            layout=go.Layout(
                title=dict(
                    text=(f"Cu Removal Surface — {OXIDE_DOSE_G:.0f}g Fe₂O₃, "
                          f"{STEEL_MASS_KG} kg steel<br>"
                          f"<span style='font-size:14px; color:{phase_color};'>"
                          f"T = {T} K ({phase})"
                          f"{'  —  LIQUIDUS CROSSED' if T == 1823 else ''}"
                          f"</span>"),
                ),
            ),
        ))

    fig.frames = frames

    # ── Layout ───────────────────────────────────────────────────
    fig.update_layout(
        title=dict(
            text=(f"Cu Removal Surface — {OXIDE_DOSE_G:.0f}g Fe₂O₃, "
                  f"{STEEL_MASS_KG} kg steel<br>"
                  f"<span style='font-size:14px; color:#888;'>"
                  f"Gray = solid steel ({T_solid} K). "
                  f"Colored = current T. Purple plane = target ({TARGET_REMOVAL:.0f}%)."
                  f"</span>"),
            font=dict(size=16),
        ),
        scene=dict(
            xaxis=dict(title="Contact Time (min)", tickvals=times_min),
            yaxis=dict(title="Particle Radius (um)", tickvals=radii),
            zaxis=dict(title="Cu Removal (%)", range=[0, 105]),
            camera=dict(
                eye=dict(x=1.8, y=-1.5, z=0.8),
                up=dict(x=0, y=0, z=1),
            ),
            aspectratio=dict(x=1.2, y=1.2, z=0.8),
        ),
        width=950,
        height=700,
        # Play/pause buttons
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=-0.05,
            x=0.5,
            xanchor="center",
            buttons=[
                dict(
                    label="▶ Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=1000, redraw=True),
                        fromcurrent=True,
                        transition=dict(duration=400),
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
                font=dict(size=13),
            ),
            transition=dict(duration=400),
            pad=dict(b=10, t=40),
            len=0.9,
            x=0.05,
            y=-0.02,
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
    )

    out_html = FIG_DIR / "cu_removal_3d.html"
    fig.write_html(str(out_html), include_plotlyjs=True, full_html=True)
    print(f"Saved: {out_html} ({out_html.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
