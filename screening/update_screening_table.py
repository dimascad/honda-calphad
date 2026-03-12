"""
Update screening table after new TC-Python data is available.

Reads oxide_gibbs_energies.csv, computes reaction dG for ALL oxides,
updates the CSV and rebuilds the Excel file.

Run this locally after copying updated CSV from OSU VM.
"""

import csv
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "oxide_gibbs_energies.csv"
CSV_OUT = SCRIPT_DIR / "screening_table.csv"

# All 10 screening oxides with their properties
OXIDES = [
    # cost_per_g = industrial bulk price in $/g; CAS = for SDS lookup
    {"name": "MgO",   "formula": "MgO",   "col": "dG_MgO_per_O2",   "density": 3.58, "Tm": 2852, "tox": "Low",                                          "cost": "$0.0003/g", "cost_per_g": 0.0003, "CAS": "1309-48-4"},
    {"name": "Al₂O₃", "formula": "Al2O3", "col": "dG_Al2O3_per_O2", "density": 3.95, "Tm": 2072, "tox": "Low",                                          "cost": "$0.0005/g", "cost_per_g": 0.0005, "CAS": "1344-28-1"},
    {"name": "CaO",   "formula": "CaO",   "col": "dG_CaO_per_O2",   "density": 3.34, "Tm": 2613, "tox": "Low",                                          "cost": "$0.0002/g", "cost_per_g": 0.0002, "CAS": "1305-78-8"},
    {"name": "ZrO₂",  "formula": "ZrO2",  "col": "dG_ZrO2_per_O2",  "density": 5.68, "Tm": 2715, "tox": "Low",                                          "cost": "$0.035/g",  "cost_per_g": 0.035,  "CAS": "1314-23-4"},
    {"name": "Cr₂O₃", "formula": "Cr2O3", "col": "dG_Cr2O3_per_O2", "density": 5.22, "Tm": 2435, "tox": "Moderate — Cr(VI) risk if oxidized",            "cost": "$0.005/g",  "cost_per_g": 0.005,  "CAS": "1308-38-9"},
    {"name": "TiO₂",  "formula": "TiO2",  "col": "dG_TiO2_per_O2",  "density": 4.23, "Tm": 1843, "tox": "Low",                                          "cost": "$0.003/g",  "cost_per_g": 0.003,  "CAS": "13463-67-7"},
    {"name": "SiO₂",  "formula": "SiO2",  "col": "dG_SiO2_per_O2",  "density": 2.65, "Tm": 1713, "tox": "Low (crystalline = inhalation hazard)",          "cost": "$0.00005/g","cost_per_g": 0.00005,"CAS": "7631-86-9"},
    {"name": "MnO",   "formula": "MnO",   "col": "dG_MnO_per_O2",   "density": 5.43, "Tm": 1842, "tox": "Low",                                          "cost": "$0.005/g",  "cost_per_g": 0.005,  "CAS": "1344-43-0"},
    {"name": "FeO",   "formula": "FeO",   "col": "dG_FeO_per_O2",   "density": 5.74, "Tm": 1377, "tox": "Low",                                          "cost": "$0.0009/g", "cost_per_g": 0.0009, "CAS": "1345-25-1"},
    {"name": "CuO",   "formula": "CuO",   "col": "dG_CuO_per_O2",   "density": 6.31, "Tm": 1326, "tox": "Moderate — aquatic toxin",                      "cost": "$0.008/g",  "cost_per_g": 0.008,  "CAS": "1317-38-0"},
    # --- Moonshot oxides (Mar 2026) ---
    {"name": "NiO",   "formula": "NiO",   "col": "dG_NiO_per_O2",   "density": 6.67, "Tm": 1955, "tox": "HIGH — IARC Group 1 carcinogen (inhalation)",    "cost": "$0.016/g",  "cost_per_g": 0.016,  "CAS": "1313-99-1"},
    {"name": "CoO",   "formula": "CoO",   "col": "dG_CoO_per_O2",   "density": 6.44, "Tm": 1830, "tox": "HIGH — Carc. 1B, reproductive toxin",            "cost": "$0.018/g",  "cost_per_g": 0.018,  "CAS": "1307-96-6"},
    {"name": "PbO",   "formula": "PbO",   "col": "dG_PbO_per_O2",   "density": 9.53, "Tm":  888, "tox": "HIGH — Repr. 1A, cumulative neurotoxin",          "cost": "$0.004/g",  "cost_per_g": 0.004,  "CAS": "1317-36-8"},
    {"name": "B₂O₃",  "formula": "B2O3",  "col": "dG_B2O3_per_O2",  "density": 2.55, "Tm":  450, "tox": "Moderate — Repr. 1B reproductive toxicant",       "cost": "$0.003/g",  "cost_per_g": 0.003,  "CAS": "1303-86-2"},
    {"name": "V₂O₅",  "formula": "V2O5",  "col": "dG_V2O5_per_O2",  "density": 3.36, "Tm":  690, "tox": "HIGH — Carc. 1B, mutagenic, acute toxic",         "cost": "$0.011/g",  "cost_per_g": 0.011,  "CAS": "1314-62-1"},
    {"name": "La₂O₃", "formula": "La2O3", "col": "dG_La2O3_per_O2", "density": 6.51, "Tm": 2315, "tox": "Low-Moderate — mild pulmonary risk",               "cost": "$0.010/g",  "cost_per_g": 0.010,  "CAS": "1312-81-8"},
    {"name": "CeO₂",  "formula": "CeO2",  "col": "dG_CeO2_per_O2",  "density": 7.22, "Tm": 2400, "tox": "Low",                                            "cost": "$0.006/g",  "cost_per_g": 0.006,  "CAS": "1306-38-3"},
]

TEMPS_K = [1000, 1500, 1800]  # ~727, ~1227, ~1527 C
CU2O_COL = "dG_Cu2O_per_O2"


def main():
    # Load TC-Python data
    with open(CSV_IN) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    T_vals = np.array([float(r["T_K"]) for r in rows])

    # Get Cu2O reference at each temperature
    cu2o_vals = {}
    for T in TEMPS_K:
        idx = int(np.argmin(np.abs(T_vals - T)))
        cu2o_vals[T] = float(rows[idx][CU2O_COL])

    print("=" * 85)
    print("Screening Table — Reaction ΔG: Cu + MO_x")
    print("ΔG_rxn = ΔG_f(Cu₂O) - ΔG_f(MO_x) per mol O₂")
    print("Positive = Cu CANNOT reduce | Negative = Cu CAN reduce")
    print("=" * 85)

    results = []
    for oxide in OXIDES:
        col = oxide["col"]
        row = {
            "Oxide": oxide["name"],
            "Formula": oxide["formula"],
            "Density (g/cm³)": oxide["density"],
            "Melting Point (°C)": oxide["Tm"],
            "Floats on Steel?": "Yes" if oxide["density"] < 7.0 else "No",
            "Solid at 1527°C?": "Yes" if oxide["Tm"] > 1527 else ("No — LIQUID" if oxide["Tm"] <= 1527 else "Yes"),
        }

        has_data = col in rows[0] and rows[0][col].strip() != ''
        for T in TEMPS_K:
            T_C = T - 273
            key = f"ΔG_rxn @ {T_C}°C (kJ/mol O₂)"
            if has_data:
                idx = int(np.argmin(np.abs(T_vals - T)))
                val = rows[idx][col].strip()
                if val:
                    dG_oxide = float(val)
                    dG_rxn = (cu2o_vals[T] - dG_oxide) / 1000  # J -> kJ
                    row[key] = f"{dG_rxn:+.1f}"
                else:
                    row[key] = "TBD — needs TC-Python"
                    has_data = False
            else:
                row[key] = "TBD — needs TC-Python"

        if has_data:
            # Use 1800K value for verdict
            idx = int(np.argmin(np.abs(T_vals - 1800)))
            val = rows[idx][col].strip()
            dG_rxn_1800 = (cu2o_vals[1800] - float(val)) / 1000 if val else None
            if dG_rxn_1800 is None:
                row["Cu Can Reduce?"] = "TBD"
            elif oxide["name"] == "CuO":
                row["Cu Can Reduce?"] = "Trivially yes (Cu self-oxidation)"
            elif dG_rxn_1800 > 0:
                row["Cu Can Reduce?"] = "No"
            else:
                row["Cu Can Reduce?"] = "Yes"
        else:
            row["Cu Can Reduce?"] = "TBD"

        row["Toxicity"] = oxide["tox"]
        row["Cost / Availability"] = oxide["cost"]
        results.append(row)

    # Print table
    print(f"\n{'Oxide':<10}", end="")
    for T in TEMPS_K:
        print(f"  {'@' + str(T-273) + '°C':>18}", end="")
    print(f"  {'Verdict':>12}")
    print("-" * 75)
    for r in results:
        print(f"{r['Oxide']:<10}", end="")
        for T in TEMPS_K:
            key = f"ΔG_rxn @ {T-273}°C (kJ/mol O₂)"
            print(f"  {r[key]:>18}", end="")
        print(f"  {r['Cu Can Reduce?']:>12}")

    # Write CSV
    fieldnames = list(results[0].keys())
    with open(CSV_OUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nCSV written to: {CSV_OUT}")

    # Check for TBD entries
    tbd = [r["Oxide"] for r in results if "TBD" in str(r.get("Cu Can Reduce?", ""))]
    if tbd:
        print(f"\n*** Still need TC-Python data for: {', '.join(tbd)} ***")
    else:
        print("\nAll oxides have data. Ready to rebuild Excel with build_screening_xlsx.py")


if __name__ == "__main__":
    main()
