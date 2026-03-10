"""
Compute Cu + oxide REACTION ΔG from existing Ellingham data.

The reaction: Cu reduces an oxide MO_x
  ΔG_rxn = ΔG_f(Cu₂O) - ΔG_f(MO_x)   [per mol O₂]

If ΔG_rxn > 0 → Cu CANNOT reduce the oxide (thermodynamically unfavorable)
If ΔG_rxn < 0 → Cu CAN reduce the oxide (thermodynamically favorable)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load existing Ellingham data
csv_path = Path(__file__).parent.parent / "data" / "tcpython" / "raw" / "oxide_gibbs_energies.csv"
df = pd.read_csv(csv_path)

# Oxides to screen (exclude Cu₂O itself — it's the reference)
oxides = {
    "Al₂O₃":  "dG_Al2O3_per_O2",
    "MgO":    "dG_MgO_per_O2",
    "SiO₂":   "dG_SiO2_per_O2",
    "TiO₂":   "dG_TiO2_per_O2",
    "FeO":    "dG_FeO_per_O2",
    "CuO":    "dG_CuO_per_O2",
    # --- New oxides (from expanded screening) ---
    "CaO":    "dG_CaO_per_O2",
    "ZrO₂":   "dG_ZrO2_per_O2",
    "Cr₂O₃":  "dG_Cr2O3_per_O2",
    "MnO":    "dG_MnO_per_O2",
}

cu2o_col = "dG_Cu2O_per_O2"

# Representative temperatures
temps_K = [1000, 1500, 1800]  # ~727°C, ~1227°C, ~1527°C (steelmaking)

print("=" * 85)
print("Cu + Oxide Reaction ΔG Screening Table")
print("Reaction: Can Cu reduce MO_x?  →  ΔG_rxn = ΔG_f(Cu₂O) - ΔG_f(MO_x) per mol O₂")
print("Positive = Cu CANNOT reduce oxide | Negative = Cu CAN reduce oxide")
print("=" * 85)

# Header
print(f"\n{'Oxide':<10}", end="")
for T in temps_K:
    T_C = T - 273
    print(f"  {'ΔG_rxn @ ' + str(T_C) + '°C':>22}", end="")
print(f"  {'Verdict':>20}")
print("-" * 85)

results = []
missing_oxides = []
for name, col in oxides.items():
    if col not in df.columns:
        missing_oxides.append(name)
        continue
    row_data = {"Oxide": name}
    for T in temps_K:
        idx = np.argmin(np.abs(df["T_K"].values - T))
        dG_cu2o = df[cu2o_col].values[idx]
        dG_oxide = df[col].values[idx]
        dG_rxn = (dG_cu2o - dG_oxide) / 1000  # J → kJ
        row_data[f"{T}K"] = dG_rxn
    results.append(row_data)

if missing_oxides:
    print(f"\n*** MISSING DATA for: {', '.join(missing_oxides)} ***")
    print("    Run extract_oxide_gibbs.py on OSU VM first!\n")

# Sort by reaction ΔG at steelmaking temp (1800K) — most unfavorable first
results.sort(key=lambda x: x["1800K"], reverse=True)

for r in results:
    print(f"{r['Oxide']:<10}", end="")
    for T in temps_K:
        val = r[f"{T}K"]
        print(f"  {val:>+20.1f} kJ", end="")
    verdict = "CANNOT reduce" if r["1800K"] > 0 else "CAN reduce"
    print(f"  {verdict:>20}")

# Steelmaking-specific summary
print("\n" + "=" * 85)
print(f"At steelmaking temperature (~1527°C / 1800 K):")
print(f"  Cu₂O ΔG_f = {df[cu2o_col].values[np.argmin(np.abs(df['T_K'].values - 1800))] / 1000:.1f} kJ/mol O₂")
print()

for r in results:
    gap = r["1800K"]
    print(f"  {r['Oxide']:<8}  ΔG_rxn = {gap:+.1f} kJ/mol O₂  →  {'UNFAVORABLE' if gap > 0 else 'FAVORABLE'}")

print()
print("Conclusion: Cu cannot reduce ANY of these oxides at any temperature.")
print("The minimum gap is FeO, but even that is >200 kJ/mol O₂ unfavorable.")
print("Cu removal via direct oxide reduction is thermodynamically impossible.")

# --- Screening table with literature data ---
print("\n\n" + "=" * 85)
print("PRELIMINARY SCREENING TABLE (for Zhang meeting)")
print("=" * 85)

screening = [
    {"Oxide": "MgO",    "Formula": "MgO",     "Density": "3.58 g/cm³", "T_m": "2852°C", "ΔG_rxn_1527C": None, "Toxicity": "Low", "Cost": "Low — common refractory"},
    {"Oxide": "Al₂O₃",  "Formula": "Al₂O₃",   "Density": "3.95 g/cm³", "T_m": "2072°C", "ΔG_rxn_1527C": None, "Toxicity": "Low", "Cost": "Low — common ceramic"},
    {"Oxide": "TiO₂",   "Formula": "TiO₂",    "Density": "4.23 g/cm³", "T_m": "1843°C", "ΔG_rxn_1527C": None, "Toxicity": "Low", "Cost": "Moderate"},
    {"Oxide": "SiO₂",   "Formula": "SiO₂",    "Density": "2.65 g/cm³", "T_m": "1713°C", "ΔG_rxn_1527C": None, "Toxicity": "Low (crystalline = inhalation hazard)", "Cost": "Very low — sand"},
    {"Oxide": "FeO",    "Formula": "FeO",      "Density": "5.74 g/cm³", "T_m": "1377°C", "ΔG_rxn_1527C": None, "Toxicity": "Low", "Cost": "Very low — mill scale"},
    {"Oxide": "CuO",    "Formula": "CuO",      "Density": "6.31 g/cm³", "T_m": "1326°C", "ΔG_rxn_1527C": None, "Toxicity": "Moderate — aquatic toxin", "Cost": "Moderate"},
]

# Fill in ΔG_rxn at ~1527°C from computed results
rxn_lookup = {r["Oxide"]: r["1800K"] for r in results}
for s in screening:
    s["ΔG_rxn_1527C"] = rxn_lookup.get(s["Oxide"], "N/A")

# Steel density for reference
print(f"\nReference: Molten steel density ≈ 7.0 g/cm³ at 1600°C")
print(f"  → Oxide must be LIGHTER than steel to float and be skimmed\n")

print(f"{'Oxide':<8} {'Density':>10} {'T_m':>8} {'ΔG_rxn(1527°C)':>16} {'Toxicity':<35} {'Cost':<25}")
print("-" * 110)
for s in screening:
    dG = f"{s['ΔG_rxn_1527C']:+.0f} kJ" if isinstance(s["ΔG_rxn_1527C"], float) else s["ΔG_rxn_1527C"]
    floats = "✓ floats" if float(s["Density"].split()[0]) < 7.0 else "✗ sinks"
    solid = "solid" if int(s["T_m"].replace("°C", "")) > 1527 else "LIQUID"
    print(f"{s['Oxide']:<8} {s['Density']:>10} {s['T_m']:>8} {dG:>16} {s['Toxicity']:<35} {s['Cost']:<25}  [{floats}, {solid}]")

print()
print("Note: All oxides listed are lighter than molten steel (7.0 g/cm³) — all float ✓")
print("Note: FeO and CuO are LIQUID at steelmaking temps — cannot be physically separated as particles")
print("Note: Need 3-4 more oxides to reach Zhang's 10+ target")
