"""
Animated Cu removal parameter sweep — converges to optimal operating point.

Dashboard-style animation with:
  - Three parameter panels (T, R, t) on the left — active sweep highlighted
  - Large removal % arc gauge in the center
  - Phase banner and narrative subtitle

Three sweep phases + finale:
  1. Temperature sweep (1673→1923 K) at R=250 μm, t=5 min
  2. Radius sweep (500→25 μm) at T_opt, t=5 min
  3. Time sweep (1→30 min) at T_opt, R_opt
  4. Finale: hold on optimal

Saves as GIF. Run: python3 screening/animate_cu_removal.py
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "data" / "tcpython" / "raw"
FIG_DIR = SCRIPT_DIR.parent / "figures"
SUMMARY_CSV = RAW_DIR / "cu_removal_rate_summary.csv"

# ── Physical parameters ───────────────────────────────────────────
RHO_OXIDE = 5240       # kg/m3 Fe2O3
CU_INIT_WT = 0.30      # wt%
STEEL_MASS_KG = 0.50   # kg
OXIDE_DOSE_G = 2.0     # grams

# Colorblind palette
BLUE   = "#0077BB"
ORANGE = "#EE7733"
PURPLE = "#AA3377"
TEAL   = "#009988"
RED    = "#CC3311"
GRAY   = "#BBBBBB"
DARK   = "#2D2D2D"

FE_LIQUIDUS = 1811  # K
TARGET_REMOVAL = (1 - 0.10 / CU_INIT_WT) * 100  # 66.7%

# ── Data ──────────────────────────────────────────────────────────

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


def lookup(summary, T, R, t):
    for row in summary:
        if row["temp_K"] == T and row["radius_um"] == R and row["time_s"] == t:
            return row
    return None


# ── Frame sequence ────────────────────────────────────────────────

TEMPS = [1673, 1698, 1723, 1748, 1773, 1798, 1823, 1848, 1873, 1898, 1923]
RADII = [500, 250, 100, 50, 25]
TIMES_S = [60, 300, 600, 1800]
TIME_LABELS = {60: "1 min", 300: "5 min", 600: "10 min", 1800: "30 min"}

OPT_T, OPT_R, OPT_t = 1923, 25, 1800


def build_frames():
    """Returns list of (T, R, t, active_sweep, subtitle)"""
    frames = []

    # Phase 1: Temperature sweep
    for T in TEMPS:
        frames.append((T, 250, 300, "temp",
                        f"Step 1:  Sweeping temperature  →  {T} K"))

    # Phase 2: Radius sweep
    for R in RADII:
        frames.append((OPT_T, R, 300, "radius",
                        f"Step 2:  Sweeping particle size  →  {R} μm"))

    # Phase 3: Time sweep
    for t in TIMES_S:
        frames.append((OPT_T, OPT_R, t, "time",
                        f"Step 3:  Sweeping contact time  →  {TIME_LABELS[t]}"))

    # Finale
    for _ in range(6):
        frames.append((OPT_T, OPT_R, OPT_t, "optimal",
                        "OPTIMAL  CONFIGURATION"))

    return frames


# ── Drawing helpers ───────────────────────────────────────────────

def draw_arc_gauge(ax, pct, target_pct, is_optimal):
    """Draw a half-circle gauge from 0-100% removal."""
    ax.clear()
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-0.4, 1.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # Background arc (gray)
    theta_bg = np.linspace(np.pi, 0, 200)
    ax.plot(np.cos(theta_bg), np.sin(theta_bg), color=GRAY, lw=28, solid_capstyle="round")

    # Filled arc (colored by performance)
    if pct > 0.1:
        frac = min(pct / 100.0, 1.0)
        theta_fill = np.linspace(np.pi, np.pi * (1 - frac), max(int(200 * frac), 2))
        color = TEAL if pct >= target_pct else ORANGE if pct > 5 else RED
        ax.plot(np.cos(theta_fill), np.sin(theta_fill), color=color, lw=26,
                solid_capstyle="round")

    # Target marker
    target_angle = np.pi * (1 - target_pct / 100.0)
    tx, ty = np.cos(target_angle), np.sin(target_angle)
    ax.plot([tx * 0.78, tx * 1.22], [ty * 0.78, ty * 1.22],
            color=PURPLE, lw=3, zorder=10)
    ax.text(tx * 1.35, ty * 1.35, f"Target\n{target_pct:.0f}%",
            ha="center", va="center", fontsize=7, color=PURPLE, fontweight="bold")

    # Scale labels
    ax.text(-1.0, -0.2, "0%", ha="center", fontsize=8, color="#888888")
    ax.text(1.0, -0.2, "100%", ha="center", fontsize=8, color="#888888")
    ax.text(0, 1.15, "50%", ha="center", fontsize=8, color="#888888")

    # Big number
    weight = "bold"
    size = 38 if is_optimal else 32
    ax.text(0, 0.35, f"{pct:.1f}%", ha="center", va="center",
            fontsize=size, fontweight=weight,
            color=TEAL if pct >= target_pct else DARK)
    ax.text(0, 0.05, "Cu Removed", ha="center", va="center",
            fontsize=11, color="#666666")


def draw_param_panel(ax, label, value, unit, values_range, active, is_optimal, is_liquid=None):
    """Draw a single parameter indicator."""
    ax.clear()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")

    # Background box
    bg_color = "#FFFFCC" if is_optimal else ("#E8F4FD" if active else "#F5F5F5")
    edge_color = TEAL if is_optimal else (BLUE if active else "#DDDDDD")
    edge_width = 3 if active or is_optimal else 1
    rect = mpatches.FancyBboxPatch((0.2, 0.2), 9.6, 2.6,
                                    boxstyle="round,pad=0.3",
                                    facecolor=bg_color,
                                    edgecolor=edge_color,
                                    linewidth=edge_width)
    ax.add_patch(rect)

    # Label
    ax.text(0.8, 2.2, label, fontsize=9, color="#888888", va="center")

    # Value
    val_color = BLUE if active else DARK
    ax.text(5, 1.2, f"{value} {unit}", ha="center", va="center",
            fontsize=16, fontweight="bold", color=val_color)

    # Phase indicator for temperature
    if is_liquid is not None:
        phase_color = TEAL if is_liquid else RED
        phase_text = "LIQUID" if is_liquid else "SOLID"
        ax.text(9.2, 2.2, phase_text, ha="right", va="center",
                fontsize=8, fontweight="bold", color=phase_color)

    # Sweep arrow if active
    if active:
        ax.annotate("", xy=(9.0, 1.2), xytext=(8.2, 1.2),
                     arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))


# ── Main animation ────────────────────────────────────────────────

def main():
    summary = load_summary()
    frame_seq = build_frames()

    fig = plt.figure(figsize=(10, 7))
    fig.patch.set_facecolor("white")

    # Layout: 3 param panels on left, gauge on right
    # Top: title
    gs = fig.add_gridspec(4, 2, left=0.02, right=0.98, top=0.88, bottom=0.08,
                          hspace=0.3, wspace=0.05,
                          width_ratios=[1, 1.6], height_ratios=[1, 1, 1, 0.3])

    ax_temp = fig.add_subplot(gs[0, 0])
    ax_rad  = fig.add_subplot(gs[1, 0])
    ax_time = fig.add_subplot(gs[2, 0])
    ax_gauge = fig.add_subplot(gs[0:3, 1])
    ax_banner = fig.add_subplot(gs[3, :])

    suptitle = fig.suptitle("Cu Removal from Steel — DICTRA Optimization",
                             fontsize=15, fontweight="bold", y=0.96)
    subtitle_text = fig.text(0.5, 0.91, "", ha="center", fontsize=11, color="#555555")

    # Fixed system info
    fig.text(0.5, 0.03,
             f"{OXIDE_DOSE_G:.0f} g Fe₂O₃  •  {STEEL_MASS_KG} kg steel  •  {CU_INIT_WT} wt% Cu initial",
             ha="center", fontsize=9, color="#999999")

    def update(frame_idx):
        T, R, t, sweep, sub = frame_seq[frame_idx]
        is_opt = (sweep == "optimal")
        is_liquid = T >= 1823

        row = lookup(summary, T, R, t)
        removal = compute_removal(row["cu_captured_mg"], R) if row else 0.0

        # Parameter panels
        draw_param_panel(ax_temp, "Temperature", T, "K",
                         TEMPS, sweep == "temp", is_opt, is_liquid=is_liquid)
        draw_param_panel(ax_rad, "Particle Radius", R, "μm",
                         RADII, sweep == "radius", is_opt)
        draw_param_panel(ax_time, "Contact Time", TIME_LABELS[t], "",
                         TIMES_S, sweep == "time", is_opt)

        # Gauge
        draw_arc_gauge(ax_gauge, removal, TARGET_REMOVAL, is_opt)

        # Bottom banner
        ax_banner.clear()
        ax_banner.set_xlim(0, 10)
        ax_banner.set_ylim(0, 1)
        ax_banner.axis("off")

        if is_opt:
            subtitle_text.set_text("")
            ax_banner.text(5, 0.5, "✓  OPTIMAL FOUND", ha="center", va="center",
                           fontsize=14, fontweight="bold", color=TEAL)
        else:
            subtitle_text.set_text(sub)
            # Progress dots
            phases = ["temp", "radius", "time"]
            phase_labels = ["Temperature", "Particle Size", "Contact Time"]
            for i, (p, pl) in enumerate(zip(phases, phase_labels)):
                x = 2 + i * 3
                done = phases.index(sweep) > i if sweep in phases else True
                active = (sweep == p)
                dot_color = TEAL if done else (BLUE if active else GRAY)
                ax_banner.plot(x, 0.5, "o", color=dot_color,
                               markersize=12 if active else 8, zorder=5)
                ax_banner.text(x, 0.1, pl, ha="center", fontsize=7,
                               color=dot_color, fontweight="bold" if active else "normal")
                if i < 2:
                    ax_banner.plot([x + 0.3, x + 2.7], [0.5, 0.5],
                                   color=TEAL if done else GRAY, lw=1.5)

        return []

    n_frames = len(frame_seq)
    anim = animation.FuncAnimation(fig, update, frames=n_frames,
                                    blit=False, interval=800, repeat=True)

    out_gif = FIG_DIR / "cu_removal_sweep.gif"
    print(f"Saving {n_frames}-frame animation to {out_gif} ...")
    anim.save(str(out_gif), writer="pillow", fps=1.5, dpi=140)
    print(f"Done. {out_gif.stat().st_size / 1024:.0f} KB")

    plt.close()
    print("Opening in browser...")


if __name__ == "__main__":
    main()
