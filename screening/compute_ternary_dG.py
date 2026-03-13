"""
Post-process ternary reaction energies from TC-Python extraction.

Reads ternary_reaction_energies.csv and produces:
  1. Summary table of all ternary reactions at steelmaking temperatures
  2. Ranked list of most promising oxide candidates
  3. CSV output for downstream visualization

Run locally after copying ternary_reaction_energies.csv from OSU VM.
"""

import csv
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "ternary_reaction_energies.csv"
CSV_OUT = SCRIPT_DIR / "ternary_screening_results.csv"

# Key steelmaking temperatures
TEMPS_K = [1000, 1500, 1800]  # 727, 1227, 1527 C


def main():
    if not CSV_IN.exists():
        print(f"ERROR: {CSV_IN} not found!")
        print("Run extract_ternary_reactions.py on OSU VM first, then copy the CSV here.")
        return

    with open(CSV_IN) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("=" * 80)
    print("Ternary Reaction Screening — Cu + MOx → CuMOy")
    print("Negative dG_rxn = FAVORABLE (copper captured into ternary compound)")
    print("=" * 80)

    # Get unique products
    products = []
    seen = set()
    for r in rows:
        key = r["product"]
        if key not in seen:
            seen.add(key)
            products.append({
                "product": r["product"],
                "product_name": r["product_name"],
                "oxide": r["oxide"],
                "reaction": r["reaction"],
            })

    # Extract dG at key temperatures for each product
    results = []
    for prod_info in products:
        product = prod_info["product"]
        prod_rows = [r for r in rows if r["product"] == product]

        # Build temperature -> dG map
        T_vals = []
        dG_vals = []
        for r in prod_rows:
            T = float(r["T_K"])
            dG_str = r.get("dG_rxn_system_kJ", "").strip()
            if dG_str:
                try:
                    dG = float(dG_str)
                    T_vals.append(T)
                    dG_vals.append(dG)
                except ValueError:
                    pass

        T_arr = np.array(T_vals)
        dG_arr = np.array(dG_vals)

        entry = {
            "Product": product,
            "Name": prod_info["product_name"],
            "Oxide": prod_info["oxide"],
            "Reaction": prod_info["reaction"],
        }

        # Get dG at key temperatures
        for T_target in TEMPS_K:
            key = f"dG_rxn @ {T_target - 273}°C (kJ)"
            if len(T_arr) > 0:
                idx = int(np.argmin(np.abs(T_arr - T_target)))
                if np.abs(T_arr[idx] - T_target) < 30:  # within 30K
                    entry[key] = f"{dG_arr[idx]:+.1f}"
                else:
                    entry[key] = "No data near this T"
            else:
                entry[key] = "No data"

        # Check for ternary phase at 1800K
        rows_1800 = [r for r in prod_rows
                     if abs(float(r["T_K"]) - 1800) < 30]
        if rows_1800:
            entry["Ternary Phase Found"] = rows_1800[0].get("ternary_phase_found", "")
            entry["Stable Phases @ 1527°C"] = rows_1800[0].get("stable_phases", "")
        else:
            entry["Ternary Phase Found"] = ""
            entry["Stable Phases @ 1527°C"] = ""

        # Verdict: use 1800K value
        dG_1800_key = f"dG_rxn @ {1800 - 273}°C (kJ)"
        dG_str = entry.get(dG_1800_key, "")
        if dG_str and dG_str not in ("No data", "No data near this T"):
            dG_val = float(dG_str)
            if dG_val < -10:
                entry["Verdict"] = "FAVORABLE — Cu captured"
            elif dG_val < 0:
                entry["Verdict"] = "Marginally favorable"
            elif dG_val < 10:
                entry["Verdict"] = "Borderline"
            else:
                entry["Verdict"] = "Unfavorable"
        else:
            entry["Verdict"] = "No data"

        results.append(entry)

    # Print table
    print(f"\n{'Product':<16} ", end="")
    for T in TEMPS_K:
        print(f"  {'@' + str(T-273) + '°C':>14}", end="")
    print(f"  {'Ternary Phase':>16}  {'Verdict':<24}")
    print("-" * 110)

    for r in results:
        print(f"{r['Product']:<16} ", end="")
        for T in TEMPS_K:
            key = f"dG_rxn @ {T - 273}°C (kJ)"
            print(f"  {r[key]:>14}", end="")
        phase = r.get("Ternary Phase Found", "")
        print(f"  {(phase or '--'):>16}", end="")
        print(f"  {r['Verdict']:<24}")

    # Rank by dG at 1527°C
    print(f"\n{'='*80}")
    print("RANKING: Most Promising Oxides for Copper Capture (1527°C)")
    print("=" * 80)

    dG_key = f"dG_rxn @ {1800 - 273}°C (kJ)"
    ranked = []
    for r in results:
        v = r.get(dG_key, "")
        if v and v not in ("No data", "No data near this T"):
            ranked.append((r["Product"], float(v), r["Oxide"], r.get("Ternary Phase Found", "")))

    ranked.sort(key=lambda x: x[1])

    for i, (product, dG, oxide, phase) in enumerate(ranked, 1):
        marker = "***" if dG < 0 else "   "
        print(f"  {marker} {i:2d}. {product:<16}  dG = {dG:>+8.1f} kJ   (from {oxide})"
              f"  phase: {phase or 'not found'}")

    # Write CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(CSV_OUT, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nCSV written to: {CSV_OUT}")

    # Identify top candidates
    favorable = [r for r in ranked if r[1] < 0]
    if favorable:
        print(f"\n*** {len(favorable)} FAVORABLE reactions found! ***")
        print("These oxides can capture copper into ternary compounds:")
        for product, dG, oxide, phase in favorable:
            print(f"   {oxide} → {product}  (dG = {dG:+.1f} kJ, phase: {phase or 'check manually'})")
        print("\nRecommend these for experimental validation.")
    else:
        print("\nNo strongly favorable ternary reactions found at 1527°C.")
        print("Check lower temperatures or consider kinetic/slag mechanisms.")


if __name__ == "__main__":
    main()
