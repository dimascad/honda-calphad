#!/usr/bin/env python3
"""
Cu Partition Between Steel and Oxide Slag at Equilibrium.

For each of the 5 candidate oxides at 5 doses, sets up a realistic
steel + oxide composition at 1800K and computes equilibrium with TCOX14.
Extracts Cu content in each stable phase to determine the partition ratio
L_Cu = Cu_wt%(slag) / Cu_wt%(metal).

If L_Cu >> 1, the slag captures Cu effectively. If L_Cu ~ 1, there is no
thermodynamic preference and mass efficiency is the real differentiator.

This answers: does dG magnitude determine how much Cu the slag absorbs,
or is mass efficiency (particles per gram, Cu per mol) the real driver?

Setup: 0.5 kg steel at 0.30 wt% Cu + oxide dose (1, 2, 3, 5, 10 g)
Temperature: 1800 K (steelmaking, above liquidus)

Note on TCOX14 phase behavior: The IONIC_LIQ two-sublattice model
represents BOTH metallic liquids (vacancy-dominated anion sublattice) and
oxide slags (O2- dominated anion sublattice). At steel-like compositions
(x_O ~ 0.01), TCOX14 may predict a miscibility gap: IONIC_LIQ (metallic)
+ IONIC_LIQ#2 (slag). We classify phases by their oxygen content: metal
if x_O < 0.05, slag if x_O > 0.10.

Output: ../../data/tcpython/raw/cu_partition_equilibrium.csv

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" cu_partition_equilibrium.py
"""

import csv
import traceback
from pathlib import Path
from datetime import datetime

from tc_python import *

# =============================================================================
# Configuration
# =============================================================================
T_K = 1800      # steelmaking temperature
DATABASE = "TCOX14"

STEEL_MASS_G = 500.0    # 0.5 kg
CU_WT_PCT = 0.30        # initial Cu in steel
DOSES_G = [1, 2, 3, 5, 10]

# Atomic weights
AW = {
    "FE": 55.845, "CU": 63.546, "O": 15.999,
    "AL": 26.982, "SI": 28.086, "MN": 54.938, "V": 50.942,
}

# Oxides: (display_name, formula_dict {elem: atoms}, MW)
OXIDES = [
    ("Fe2O3", {"FE": 2, "O": 3}, 159.69),
    ("V2O5",  {"V": 2, "O": 5},  181.88),
    ("MnO",   {"MN": 1, "O": 1},  70.94),
    ("SiO2",  {"SI": 1, "O": 2},  60.08),
    ("Al2O3", {"AL": 2, "O": 3}, 101.96),
]

# Phases to probe for Cu content (comprehensive TCOX14 list)
PROBE_PHASES = [
    "LIQUID",
    "IONIC_LIQ", "IONIC_LIQ#2", "IONIC_LIQ#3",
    "FCC_A1", "BCC_A2", "HCP_A3",
    "SPINEL", "CORUNDUM", "HALITE",
    "MULLITE", "CRISTOBALITE", "TRIDYMITE",
    "CU2O", "CUPRITE", "TENORITE",
    "WUSTITE", "MAGNETITE", "HEMATITE",
    "GAS",
]

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "cu_partition_equilibrium.csv"


# =============================================================================
# Helpers
# =============================================================================

def compute_mole_fractions(oxide_formula, oxide_mw, dose_g):
    """
    Compute system mole fractions for steel + oxide mixture.

    Steel: STEEL_MASS_G of Fe-Cu alloy at CU_WT_PCT.
    Oxide: dose_g of the specified oxide.

    Returns dict of {element: mole_fraction} with uppercase TC element names.
    """
    cu_g = STEEL_MASS_G * CU_WT_PCT / 100.0
    fe_g = STEEL_MASS_G - cu_g

    moles = {"FE": fe_g / AW["FE"], "CU": cu_g / AW["CU"]}

    n_formula = dose_g / oxide_mw
    for elem, count in oxide_formula.items():
        moles[elem] = moles.get(elem, 0) + n_formula * count

    total = sum(moles.values())
    return {e: m / total for e, m in moles.items()}


def probe_stable_phases(result, phase_list):
    """
    Probe each candidate phase for stability and Cu content.

    Returns dict of {phase_name: {np, cu_wt_pct, x_cu, x_o}} for phases
    with NP > 1e-6.
    """
    found = {}
    for phase in phase_list:
        try:
            np_val = result.get_value_of("NP({})".format(phase))
            if np_val < 1e-6:
                continue

            cu_wt, x_cu, x_o = None, None, None

            try:
                cu_wt = result.get_value_of("W({},CU)".format(phase)) * 100
            except Exception:
                pass
            try:
                x_cu = result.get_value_of("X({},CU)".format(phase))
            except Exception:
                pass
            try:
                x_o = result.get_value_of("X({},O)".format(phase))
            except Exception:
                pass

            found[phase] = {
                "np": np_val,
                "cu_wt_pct": cu_wt,
                "x_cu": x_cu,
                "x_o": x_o,
            }
        except Exception:
            pass

    return found


def classify_phases(phase_data):
    """
    Classify phases as metal or slag based on oxygen content.

    Metal: x_O < 0.05 (vacancy-dominated anion sublattice = metallic)
    Slag:  x_O > 0.10 (O2-dominated = oxide melt)
    Ambiguous: 0.05 <= x_O <= 0.10 or x_O unknown -> use name heuristic

    Returns (metal_list, slag_list) of (phase_name, phase_dict) tuples.
    """
    SLAG_NAMES = {"IONIC_LIQ", "IONIC_LIQ#2", "IONIC_LIQ#3",
                  "SPINEL", "CORUNDUM", "HALITE", "MULLITE",
                  "CRISTOBALITE", "TRIDYMITE"}
    METAL_NAMES = {"LIQUID", "FCC_A1", "BCC_A2", "HCP_A3"}

    metal, slag = [], []
    for phase, d in phase_data.items():
        if d["cu_wt_pct"] is None or d["np"] < 1e-6:
            continue

        x_o = d.get("x_o")
        if x_o is not None:
            if x_o < 0.05:
                metal.append((phase, d))
            elif x_o > 0.10:
                slag.append((phase, d))
            else:
                # Ambiguous O range -> name heuristic
                if phase in SLAG_NAMES:
                    slag.append((phase, d))
                elif phase in METAL_NAMES:
                    metal.append((phase, d))
                else:
                    metal.append((phase, d))  # default to metal
        else:
            # No O data -> name heuristic
            if phase in SLAG_NAMES:
                slag.append((phase, d))
            elif phase in METAL_NAMES:
                metal.append((phase, d))

    return metal, slag


def weighted_cu(phase_list):
    """Weighted average Cu wt% across phases, weighted by phase fraction."""
    if not phase_list:
        return None, 0.0, ""
    total_np = sum(d["np"] for _, d in phase_list)
    avg_cu = sum(d["cu_wt_pct"] * d["np"] for _, d in phase_list) / total_np
    names = "+".join(p for p, _ in phase_list)
    return avg_cu, total_np, names


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("Cu PARTITION: Steel <-> Oxide Slag Equilibrium")
    print("T = {} K | {} g steel | {} wt% Cu".format(T_K, STEEL_MASS_G, CU_WT_PCT))
    print("Database: {}".format(DATABASE))
    print("Doses: {} g".format(DOSES_G))
    print("Oxides: {}".format(", ".join(ox[0] for ox in OXIDES)))
    print("Started: {}".format(datetime.now().isoformat()))
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    with TCPython() as session:
        print("Connected to Thermo-Calc\n")

        for ox_name, ox_formula, ox_mw in OXIDES:
            # Determine elements for this system
            elems = sorted(set(["FE", "CU", "O"] + list(ox_formula.keys())))
            dep_elem = "FE"  # most abundant -> dependent
            indep = [e for e in elems if e != dep_elem]

            print("=" * 60)
            print("Oxide: {}  |  Elements: {}  |  Dependent: {}".format(
                ox_name, elems, dep_elem))
            print("=" * 60)

            # Set up system once per oxide
            try:
                system = (session
                          .select_database_and_elements(DATABASE, elems)
                          .get_system())
            except Exception as e:
                print("  SYSTEM SETUP FAILED: {}".format(e))
                for dose in DOSES_G:
                    rows.append({
                        "oxide": ox_name, "dose_g": dose, "temp_K": T_K,
                        "n_phases": 0, "stable_phases": "ERROR",
                        "cu_metal_wt_pct": "", "cu_slag_wt_pct": "",
                        "L_Cu": "", "metal_phases": "", "slag_phases": "",
                        "metal_frac": "", "slag_frac": "", "a_Cu": "",
                        "notes": str(e),
                    })
                continue

            for dose in DOSES_G:
                fracs = compute_mole_fractions(ox_formula, ox_mw, dose)

                frac_str = "  ".join("x_{}={:.6f}".format(e, fracs[e])
                                     for e in sorted(fracs))
                print("\n  dose={}g: {}".format(dose, frac_str))

                try:
                    calc = system.with_single_equilibrium_calculation()
                    calc.set_condition(
                        ThermodynamicQuantity.temperature(), T_K)
                    calc.set_condition(
                        ThermodynamicQuantity.pressure(), 101325)

                    for e in indep:
                        calc.set_condition(
                            ThermodynamicQuantity.mole_fraction_of_a_component(e),
                            fracs[e])

                    result = calc.calculate()

                    # --- Get stable phases via API ---
                    try:
                        api_phases = result.get_stable_phases()
                        print("    get_stable_phases() -> {}".format(api_phases))
                    except Exception:
                        api_phases = []

                    # --- Probe phases for detailed Cu/O data ---
                    # Combine API results with our probe list
                    all_probes = list(set(PROBE_PHASES + api_phases))
                    phase_data = probe_stable_phases(result, all_probes)

                    # Print phase details
                    for ph in sorted(phase_data, key=lambda p: -phase_data[p]["np"]):
                        d = phase_data[ph]
                        cu_s = "Cu={:.4f}wt%".format(d["cu_wt_pct"]) if d["cu_wt_pct"] is not None else "Cu=?"
                        xo_s = "x_O={:.4f}".format(d["x_o"]) if d["x_o"] is not None else ""
                        print("    {:20s}  NP={:.4f}  {}  {}".format(
                            ph, d["np"], cu_s, xo_s))

                    # --- Classify and compute partition ---
                    metal, slag = classify_phases(phase_data)
                    cu_m, np_m, nm_m = weighted_cu(metal)
                    cu_s, np_s, nm_s = weighted_cu(slag)

                    L_cu = None
                    if cu_m is not None and cu_s is not None and cu_m > 1e-10:
                        L_cu = cu_s / cu_m

                    if cu_m is not None:
                        print("    -> Metal ({}): Cu = {:.4f} wt%, frac = {:.4f}".format(
                            nm_m, cu_m, np_m))
                    else:
                        print("    -> No metal phase identified")
                    if cu_s is not None:
                        print("    -> Slag  ({}): Cu = {:.4f} wt%, frac = {:.4f}".format(
                            nm_s, cu_s, np_s))
                    else:
                        print("    -> No slag phase identified")
                    if L_cu is not None:
                        print("    -> L_Cu (slag/metal) = {:.2f}".format(L_cu))

                    # --- System-level Cu activity ---
                    try:
                        a_cu = result.get_value_of("AC(CU)")
                    except Exception:
                        a_cu = None

                    # --- Build row ---
                    notes = ""
                    if not metal and not slag:
                        notes = "Could not classify phases"
                    elif not metal:
                        notes = "No metal phase (all oxide?)"
                    elif not slag:
                        notes = "No slag phase (all metal?)"

                    rows.append({
                        "oxide": ox_name,
                        "dose_g": dose,
                        "temp_K": T_K,
                        "n_phases": len(phase_data),
                        "stable_phases": "; ".join(sorted(phase_data.keys())),
                        "cu_metal_wt_pct": "{:.6f}".format(cu_m) if cu_m is not None else "",
                        "cu_slag_wt_pct": "{:.6f}".format(cu_s) if cu_s is not None else "",
                        "L_Cu": "{:.4f}".format(L_cu) if L_cu is not None else "",
                        "metal_phases": nm_m,
                        "slag_phases": nm_s,
                        "metal_frac": "{:.6f}".format(np_m),
                        "slag_frac": "{:.6f}".format(np_s),
                        "a_Cu": "{:.6e}".format(a_cu) if a_cu is not None else "",
                        "notes": notes,
                    })

                except Exception as e:
                    print("    FAILED: {}".format(e))
                    traceback.print_exc()
                    rows.append({
                        "oxide": ox_name, "dose_g": dose, "temp_K": T_K,
                        "n_phases": 0, "stable_phases": "ERROR",
                        "cu_metal_wt_pct": "", "cu_slag_wt_pct": "",
                        "L_Cu": "", "metal_phases": "", "slag_phases": "",
                        "metal_frac": "", "slag_frac": "", "a_Cu": "",
                        "notes": str(e),
                    })

    # =========================================================================
    # Write CSV
    # =========================================================================
    if rows:
        fieldnames = [
            "oxide", "dose_g", "temp_K", "n_phases", "stable_phases",
            "cu_metal_wt_pct", "cu_slag_wt_pct", "L_Cu",
            "metal_phases", "slag_phases", "metal_frac", "slag_frac",
            "a_Cu", "notes",
        ]
        with open(str(OUTPUT_FILE), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print("\n" + "=" * 70)
        print("Saved {} rows -> {}".format(len(rows), OUTPUT_FILE))
        print("Finished: {}".format(datetime.now().isoformat()))
        print("=" * 70)

        # Summary table
        print("\nSUMMARY:")
        print("{:8s}  {:>6s}  {:>10s}  {:>10s}  {:>6s}  {:>10s}  {}".format(
            "Oxide", "Dose", "Cu(metal)", "Cu(slag)", "L_Cu", "a_Cu", "Notes"))
        print("-" * 70)
        for r in rows:
            print("{:8s}  {:>5s}g  {:>10s}  {:>10s}  {:>6s}  {:>10s}  {}".format(
                r["oxide"],
                str(r["dose_g"]),
                r["cu_metal_wt_pct"][:8] if r["cu_metal_wt_pct"] else "-",
                r["cu_slag_wt_pct"][:8] if r["cu_slag_wt_pct"] else "-",
                r["L_Cu"][:6] if r["L_Cu"] else "-",
                r["a_Cu"][:10] if r["a_Cu"] else "-",
                r["notes"],
            ))
    else:
        print("\nNo results to write!")


if __name__ == "__main__":
    main()
