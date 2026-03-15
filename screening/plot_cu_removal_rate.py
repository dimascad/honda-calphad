"""
Plot DICTRA Cu removal rate results.

Reads cu_removal_rate_profiles.csv and cu_removal_rate_summary.csv
(now with temperature sweep) to produce four figures:
  1. Cu concentration profiles (wt% vs distance from particle surface)
  2. Cu captured per particle vs contact time
  3. System-scale Cu removal (%) for a 2g Fe2O3 dose in 0.5 kg steel
  4. Temperature effect: Cu capture vs T showing solid/liquid transition

Colorblind-friendly palette per CLAUDE.md.

Run locally after copying CSVs from OSU VM.
"""

import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "data" / "tcpython" / "raw"
FIG_DIR = SCRIPT_DIR.parent / "figures"

PROFILES_CSV = RAW_DIR / "cu_removal_rate_profiles.csv"
SUMMARY_CSV = RAW_DIR / "cu_removal_rate_summary.csv"

# ── Physical parameters (must match cu_removal_rate.py) ──────────────
RHO_OXIDE = 5240       # kg/m3 for Fe2O3
CU_INIT_WT = 0.30      # wt%
STEEL_MASS_KG = 0.50   # kg
OXIDE_DOSE_G = 50.0    # grams of Fe2O3

# Reference temperature for Figs 1-3 (closest liquid temp to 1800K)
T_REF = 1823  # K — first liquid temperature in sweep

# ── Colorblind palette ───────────────────────────────────────────────
COLORS_BY_TIME = {
    60:   "#0077BB",  # blue
    300:  "#EE7733",  # orange
    600:  "#AA3377",  # purple
    1800: "#009988",  # teal
}
LABELS_BY_TIME = {
    60: "1 min", 300: "5 min", 600: "10 min", 1800: "30 min",
}
LSTYLES_BY_TIME = {
    60: "-", 300: "--", 600: ":", 1800: "-.",
}

COLORS_BY_RADIUS = {
    25:  "#0077BB",
    50:  "#EE7733",
    100: "#AA3377",
    250: "#009988",
    500: "#EE3377",
}
MARKERS_BY_RADIUS = {
    25: "o", 50: "s", 100: "^", 250: "D", 500: "v",
}


# ── Load data ────────────────────────────────────────────────────────

def load_profiles():
    rows = []
    with open(PROFILES_CSV) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "temp_K": int(r["temp_K"]),
                "radius_um": int(r["radius_um"]),
                "time_s": int(r["time_s"]),
                "dist_um": float(r["distance_from_surface_um"]),
                "cu_wt": float(r["cu_wt_pct"]),
            })
    return rows


def load_summary():
    rows = []
    with open(SUMMARY_CSV) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "temp_K": int(r["temp_K"]),
                "phase": r["phase"],
                "radius_um": int(r["radius_um"]),
                "time_s": int(r["time_s"]),
                "time_label": r["time_label"],
                "cu_captured_mg": float(r["cu_captured_mg"]),
                "depletion_um": float(r["depletion_depth_um"]),
            })
    return rows


# ── Figure 1: Cu concentration profiles ─────────────────────────────

def plot_profiles(profiles):
    """Single panel: Cu vs distance at all 4 times for R=100 um."""
    r_um = 100
    fig, ax = plt.subplots(figsize=(7, 5))

    for t_s in [60, 300, 600, 1800]:
        pts = [p for p in profiles
               if p["temp_K"] == T_REF and p["radius_um"] == r_um
               and p["time_s"] == t_s]
        pts.sort(key=lambda p: p["dist_um"])
        dist = [p["dist_um"] for p in pts]
        cu = [p["cu_wt"] for p in pts]

        ax.plot(dist, cu,
                color=COLORS_BY_TIME[t_s],
                linestyle=LSTYLES_BY_TIME[t_s],
                linewidth=2.0,
                label=LABELS_BY_TIME[t_s])

    # Shade the depletion zone for 30 min case
    pts_30 = [p for p in profiles
              if p["temp_K"] == T_REF and p["radius_um"] == r_um
              and p["time_s"] == 1800]
    pts_30.sort(key=lambda p: p["dist_um"])
    dist_30 = [p["dist_um"] for p in pts_30]
    cu_30 = [p["cu_wt"] for p in pts_30]
    ax.fill_between(dist_30, cu_30, CU_INIT_WT, alpha=0.08, color="#009988")

    ax.axhline(CU_INIT_WT, color="gray", linestyle="--", alpha=0.5, linewidth=1)
    ax.text(1600, CU_INIT_WT + 0.005, "Bulk: 0.30 wt%",
            fontsize=9, color="gray", ha="center")

    ax.axhline(0.10, color="gray", linestyle=":", alpha=0.4, linewidth=1)
    ax.text(1600, 0.105, "Target: 0.10 wt%",
            fontsize=9, color="gray", ha="center")

    ax.set_xlabel("Distance from particle surface ($\\mu$m)", fontsize=11)
    ax.set_ylabel("Cu (wt%)", fontsize=11)
    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 0.34)
    ax.set_title("Cu Depletion Profile Around Fe$_2$O$_3$ Particle "
                 "(R=100 $\\mu$m, %d K)" % T_REF,
                 fontsize=12, fontweight="bold")
    ax.legend(title="Contact time", fontsize=10, title_fontsize=10,
              loc="lower right", framealpha=0.9)

    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    ax.minorticks_on()
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / ("cu_removal_profiles." + ext),
                    dpi=300, bbox_inches="tight")
    print("Saved cu_removal_profiles.png/pdf")
    plt.close(fig)


# ── Figure 2: Cu captured per particle vs time ──────────────────────

def plot_capture_per_particle(summary):
    """Cu captured (mg) per particle vs contact time for all 5 radii."""
    fig, ax = plt.subplots(figsize=(7, 5))

    data = [s for s in summary if s["temp_K"] == T_REF]
    radii = sorted(set(r["radius_um"] for r in data))
    for r_um in radii:
        pts = [s for s in data if s["radius_um"] == r_um]
        pts.sort(key=lambda s: s["time_s"])
        times = [s["time_s"] / 60 for s in pts]
        captured = [s["cu_captured_mg"] for s in pts]

        ax.plot(times, captured,
                color=COLORS_BY_RADIUS[r_um],
                marker=MARKERS_BY_RADIUS[r_um],
                markersize=6,
                linewidth=1.8,
                label="%d $\\mu$m" % r_um)

    ax.set_xlabel("Contact time (min)", fontsize=11)
    ax.set_ylabel("Cu captured per particle (mg)", fontsize=11)
    ax.set_title("Cu Capture Rate by Particle Size (%d K, Fe$_2$O$_3$)" % T_REF,
                 fontsize=12, fontweight="bold")
    ax.legend(title="Particle radius", fontsize=9, title_fontsize=10)

    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    ax.minorticks_on()
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / ("cu_capture_per_particle." + ext),
                    dpi=300, bbox_inches="tight")
    print("Saved cu_capture_per_particle.png/pdf")
    plt.close(fig)


# ── Figure 3: System-scale removal ──────────────────────────────────

def plot_system_removal(summary):
    """2-panel: (left) fixed dose, vary radius; (right) fixed radius, vary dose."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    data = [s for s in summary if s["temp_K"] == T_REF]
    total_cu_mg = STEEL_MASS_KG * 1000 * CU_INIT_WT / 100 * 1000
    target_pct = (CU_INIT_WT - 0.10) / CU_INIT_WT * 100

    # ── Left panel: 2g dose, all radii ───────────────────────────────
    dose_g = 2.0
    radii = sorted(set(r["radius_um"] for r in data))
    for r_um in radii:
        pts = [s for s in data if s["radius_um"] == r_um]
        pts.sort(key=lambda s: s["time_s"])
        times = [s["time_s"] / 60 for s in pts]

        r_m = r_um * 1e-6
        v_particle = (4 / 3) * math.pi * r_m ** 3
        m_particle_g = RHO_OXIDE * v_particle * 1000
        n_particles = dose_g / m_particle_g

        removal_pct = []
        for s in pts:
            total_captured = s["cu_captured_mg"] * n_particles
            pct = min(total_captured / total_cu_mg * 100, 100)
            removal_pct.append(pct)

        ax1.plot(times, removal_pct,
                 color=COLORS_BY_RADIUS[r_um],
                 marker=MARKERS_BY_RADIUS[r_um],
                 markersize=7, linewidth=2.0,
                 label="%d $\\mu$m" % r_um)

    ax1.axhline(target_pct, color="gray", linestyle="--", alpha=0.5,
                linewidth=1.2)
    ax1.text(16, target_pct + 2, "Target: 0.10 wt%",
             fontsize=9, color="gray", style="italic")

    ax1.set_xlabel("Contact time (min)", fontsize=11)
    ax1.set_ylabel("Cu removal (%)", fontsize=11)
    ax1.set_ylim(0, 105)
    ax1.set_title("Effect of Particle Size (2 g Fe$_2$O$_3$)",
                  fontsize=12, fontweight="bold")
    ax1.legend(title="Particle radius", fontsize=9, title_fontsize=10)

    # ── Right panel: R=100 um, vary dose ─────────────────────────────
    r_um_fixed = 100
    doses_g = [0.5, 1, 2, 5, 10]
    dose_colors = ["#EE3377", "#AA3377", "#0077BB", "#EE7733", "#009988"]
    dose_markers = ["v", "^", "o", "s", "D"]

    for dose_g, color, marker in zip(doses_g, dose_colors, dose_markers):
        r_m = r_um_fixed * 1e-6
        v_particle = (4 / 3) * math.pi * r_m ** 3
        m_particle_g = RHO_OXIDE * v_particle * 1000
        n_particles = dose_g / m_particle_g

        pts = [s for s in data if s["radius_um"] == r_um_fixed]
        pts.sort(key=lambda s: s["time_s"])
        times = [s["time_s"] / 60 for s in pts]

        removal_pct = []
        for s in pts:
            total_captured = s["cu_captured_mg"] * n_particles
            pct = min(total_captured / total_cu_mg * 100, 100)
            removal_pct.append(pct)

        ax2.plot(times, removal_pct,
                 color=color, marker=marker,
                 markersize=7, linewidth=2.0,
                 label="%.1f g" % dose_g if dose_g < 1 else "%d g" % dose_g)

    ax2.axhline(target_pct, color="gray", linestyle="--", alpha=0.5,
                linewidth=1.2)
    ax2.text(16, target_pct + 2, "Target: 0.10 wt%",
             fontsize=9, color="gray", style="italic")

    ax2.set_xlabel("Contact time (min)", fontsize=11)
    ax2.set_ylabel("Cu removal (%)", fontsize=11)
    ax2.set_ylim(0, 105)
    ax2.set_title("Effect of Oxide Dose (R=100 $\\mu$m)",
                  fontsize=12, fontweight="bold")
    ax2.legend(title="Fe$_2$O$_3$ dose", fontsize=9, title_fontsize=10)

    for ax in (ax1, ax2):
        ax.grid(True, which="major", alpha=0.3)
        ax.grid(True, which="minor", alpha=0.1)
        ax.minorticks_on()
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.suptitle("Cu Removal from 0.5 kg Steel at %d K (DICTRA)" % T_REF,
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / ("cu_removal_system_scale." + ext),
                    dpi=300, bbox_inches="tight")
    print("Saved cu_removal_system_scale.png/pdf")
    plt.close(fig)


# ── Figure 4: Temperature effect ────────────────────────────────────

def plot_temperature_effect(summary):
    """2-panel: (left) Cu capture vs T for R=100um at all times;
    (right) system-scale removal vs T at t=30 min for all radii.

    Shows the ~260x jump at the solid/liquid transition.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    temps = sorted(set(s["temp_K"] for s in summary))

    # ── Left panel: Cu/particle vs T, R=100um, all times ────────────
    for t_s in [60, 300, 600, 1800]:
        pts = [s for s in summary
               if s["radius_um"] == 100 and s["time_s"] == t_s]
        pts.sort(key=lambda s: s["temp_K"])
        tt = [s["temp_K"] for s in pts]
        cc = [s["cu_captured_mg"] for s in pts]

        ax1.plot(tt, cc,
                 color=COLORS_BY_TIME[t_s],
                 linestyle=LSTYLES_BY_TIME[t_s],
                 marker="o", markersize=5, linewidth=2.0,
                 label=LABELS_BY_TIME[t_s])

    # Shade the liquid region
    ax1.axvspan(min(t for t in temps if t >= 1823), max(temps),
                alpha=0.06, color="#0077BB")
    ax1.axvline(1811, color="gray", linestyle=":", alpha=0.5, linewidth=1)
    ax1.text(1811, ax1.get_ylim()[1] * 0.95 if ax1.get_ylim()[1] > 0 else 0.05,
             "Fe liquidus", fontsize=8, color="gray", ha="center",
             rotation=90, va="top")

    ax1.set_xlabel("Temperature (K)", fontsize=11)
    ax1.set_ylabel("Cu captured per particle (mg)", fontsize=11)
    ax1.set_yscale("log")
    ax1.set_title("Cu Capture vs Temperature (R=100 $\\mu$m)",
                  fontsize=12, fontweight="bold")
    ax1.legend(title="Contact time", fontsize=9, title_fontsize=10)

    ax1.grid(True, which="major", alpha=0.3)
    ax1.grid(True, which="minor", alpha=0.1)
    ax1.minorticks_on()
    for spine in ax1.spines.values():
        spine.set_visible(False)

    # ── Right panel: system removal vs T, t=30min, all radii ────────
    total_cu_mg = STEEL_MASS_KG * 1000 * CU_INIT_WT / 100 * 1000
    target_pct = (CU_INIT_WT - 0.10) / CU_INIT_WT * 100
    dose_g = 2.0

    radii = sorted(set(s["radius_um"] for s in summary))
    for r_um in radii:
        pts = [s for s in summary
               if s["radius_um"] == r_um and s["time_s"] == 1800]
        pts.sort(key=lambda s: s["temp_K"])
        tt = [s["temp_K"] for s in pts]

        r_m = r_um * 1e-6
        v_particle = (4 / 3) * math.pi * r_m ** 3
        m_particle_g = RHO_OXIDE * v_particle * 1000
        n_particles = dose_g / m_particle_g

        removal = [min(s["cu_captured_mg"] * n_particles / total_cu_mg * 100,
                       100) for s in pts]

        ax2.plot(tt, removal,
                 color=COLORS_BY_RADIUS[r_um],
                 marker=MARKERS_BY_RADIUS[r_um],
                 markersize=6, linewidth=2.0,
                 label="%d $\\mu$m" % r_um)

    ax2.axhline(target_pct, color="gray", linestyle="--", alpha=0.5,
                linewidth=1.2)
    ax2.text(1700, target_pct + 2, "Target: 0.10 wt%",
             fontsize=9, color="gray", style="italic")

    ax2.axvspan(min(t for t in temps if t >= 1823), max(temps),
                alpha=0.06, color="#0077BB")
    ax2.axvline(1811, color="gray", linestyle=":", alpha=0.5, linewidth=1)
    ax2.text(1815, 5, "Fe liquidus", fontsize=8, color="gray", rotation=90)

    ax2.set_xlabel("Temperature (K)", fontsize=11)
    ax2.set_ylabel("Cu removal (%)", fontsize=11)
    ax2.set_ylim(0, 105)
    ax2.set_title("System Removal vs Temperature (t=30 min, 2 g Fe$_2$O$_3$)",
                  fontsize=12, fontweight="bold")
    ax2.legend(title="Particle radius", fontsize=9, title_fontsize=10)

    ax2.grid(True, which="major", alpha=0.3)
    ax2.grid(True, which="minor", alpha=0.1)
    ax2.minorticks_on()
    for spine in ax2.spines.values():
        spine.set_visible(False)

    fig.suptitle("Temperature Effect on Cu Removal (DICTRA, 0.5 kg steel)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / ("cu_removal_temperature_effect." + ext),
                    dpi=300, bbox_inches="tight")
    print("Saved cu_removal_temperature_effect.png/pdf")
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading DICTRA Cu removal rate data...")
    profiles = load_profiles()
    summary = load_summary()
    print("  Profiles: %d points" % len(profiles))
    print("  Summary:  %d rows" % len(summary))

    temps = sorted(set(s["temp_K"] for s in summary))
    print("  Temperatures: %s" % temps)
    print("  Reference T for Figs 1-3: %d K" % T_REF)
    print()

    FIG_DIR.mkdir(exist_ok=True)

    plot_profiles(profiles)
    plot_capture_per_particle(summary)
    plot_system_removal(summary)
    plot_temperature_effect(summary)

    print()
    print("Done. 4 figures saved to %s" % FIG_DIR)
