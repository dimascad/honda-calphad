#!/usr/bin/env python3
"""
Oxide Decision Matrix: multi-criteria radar chart for the 5 candidate oxides.

Each oxide is scored on 5 axes (all oriented so bigger polygon = better):
  1. |dG| — thermodynamic driving force (kJ/mol). Stronger = more likely to proceed.
  2. Cu capacity — grams of Cu captured per gram of oxide (stoichiometric efficiency).
  3. Particle density — scored as 1/rho so lower density = higher score (more particles/g).
  4. Melting point — higher = stays solid longer at steelmaking temps (easier to handle).
  5. Dose efficiency — scored as 1/min_dose so less oxide needed = higher score.

No single oxide wins on all axes. Fe₂O₃ and V₂O₅ dominate thermodynamics but
SiO₂ dominates stoichiometric efficiency. Al₂O₃ has the highest melting point
but weakest dG. This tradeoff is the whole point of the radar chart.

Outputs: figures/oxide_decision_matrix.png, .pdf
Run: python3 screening/visualizations/oxide_decision_matrix.py
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FIG_DIR = SCRIPT_DIR.parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Oxide data ─────────────────────────────────────────────────────
# (name, dG_kJ, cu_per_mol, MW_g/mol, rho_kg/m3, mp_C, color)
OXIDES = [
    ("Fe₂O₃",  -111.9, 1.0, 159.69, 5240, 1565, "#0077BB"),
    ("V₂O₅",   -109.2, 3.0, 181.88, 3357,  690, "#EE7733"),
    ("MnO",     -63.5, 0.5,  70.94, 5430, 1945, "#AA3377"),
    ("SiO₂",    -50.2, 2.0,  60.08, 2650, 1713, "#009988"),
    ("Al₂O₃",   -35.7, 1.0, 101.96, 3950, 2072, "#CC3311"),
]

# ── Criteria ───────────────────────────────────────────────────────
CRITERIA = ["|ΔG| (kJ/mol)", "Cu capacity\n(g Cu / g oxide)",
            "Particle count\n(1/density)", "Melting point\n(°C)",
            "Dose efficiency\n(1/min dose)"]


def compute_scores():
    """Compute raw scores for each oxide on each criterion."""
    raw = []
    for name, dG, cu_per_mol, mw, rho, mp, color in OXIDES:
        cu_per_g = cu_per_mol * 63.546 / mw
        total_cu_g = 1.5   # 1500 mg in 0.5 kg steel at 0.30 wt%
        min_dose = (total_cu_g * 0.667) / cu_per_g
        raw.append({
            "name": name,
            "color": color,
            "scores": [
                abs(dG),        # |dG|
                cu_per_g,       # Cu capacity
                1 / rho,        # particle count proxy
                mp,             # melting point
                1 / min_dose,   # dose efficiency
            ],
        })
    return raw


def normalize_scores(raw_data):
    """Min-max normalize each criterion to 0.1–1.0 range."""
    n_criteria = len(raw_data[0]["scores"])
    # Find min/max per criterion
    for c in range(n_criteria):
        vals = [d["scores"][c] for d in raw_data]
        lo, hi = min(vals), max(vals)
        for d in raw_data:
            if hi > lo:
                d["scores"][c] = 0.1 + 0.9 * (d["scores"][c] - lo) / (hi - lo)
            else:
                d["scores"][c] = 0.55  # all equal
    return raw_data


def main():
    raw = compute_scores()

    # Print raw values
    print(f"{'Oxide':<8}", end="")
    for c in CRITERIA:
        print(f"  {c.replace(chr(10), ' '):>20}", end="")
    print()
    print("-" * 110)
    for d in raw:
        print(f"{d['name']:<8}", end="")
        for s in d["scores"]:
            print(f"  {s:>20.4f}", end="")
        print()

    # Normalize
    data = normalize_scores(raw)

    print("\nNormalized (0.1–1.0):")
    for d in data:
        print(f"  {d['name']:<8}: {[f'{s:.2f}' for s in d['scores']]}")

    # ── Radar chart ────────────────────────────────────────────────
    n_criteria = len(CRITERIA)
    angles = np.linspace(0, 2 * np.pi, n_criteria, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for d in data:
        values = d["scores"] + d["scores"][:1]  # close
        ax.plot(angles, values, "o-", linewidth=2, markersize=5,
                color=d["color"], label=d["name"], zorder=3)
        ax.fill(angles, values, alpha=0.08, color=d["color"], zorder=2)

    # ── Axis labels ────────────────────────────────────────────────
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(CRITERIA, fontsize=10, ha="center")

    # Adjust label padding
    for label, angle in zip(ax.get_xticklabels(), angles[:-1]):
        if angle in (0,):
            label.set_ha("center")
        elif 0 < angle < np.pi:
            label.set_ha("left")
        elif angle == np.pi:
            label.set_ha("center")
        else:
            label.set_ha("right")

    # ── Radial grid ────────────────────────────────────────────────
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0.25, 0.50, 0.75, 1.00])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7,
                        color="#888888")
    ax.yaxis.grid(True, alpha=0.3)
    ax.xaxis.grid(True, alpha=0.3)

    # ── Legend ─────────────────────────────────────────────────────
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.10),
              fontsize=10, framealpha=0.9)

    ax.set_title(
        "Oxide Decision Matrix\n"
        "Multi-Criteria Comparison of 5 Candidate Oxides",
        fontsize=13, fontweight="bold", pad=25,
    )

    plt.tight_layout()

    for ext in ("png", "pdf"):
        out = FIG_DIR / f"oxide_decision_matrix.{ext}"
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print(f"Saved: {out}")

    plt.close()


if __name__ == "__main__":
    main()
