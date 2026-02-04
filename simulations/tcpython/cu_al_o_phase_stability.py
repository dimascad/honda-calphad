"""
Cu-Al-O Phase Stability Calculations
=====================================
Calculates equilibrium phases in the Cu-Al-O system across temperature range.
Identifies stability regions for CuAlO2 (delafossite) and CuAl2O4 (spinel).

Run on OSU lab machine:
    "C:\Program Files\Thermo-Calc\2025b\python\python.exe" simulations\tcpython\cu_al_o_phase_stability.py

Output: data/tcpython/raw/cu_al_o_phases.csv
"""

from tc_python import *
import csv
import os
from datetime import datetime

# Output path (relative to script location)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'data', 'tcpython', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'cu_al_o_phases.csv')

# Calculation parameters
TEMPERATURES_C = range(800, 1501, 50)  # 800-1500°C in 50°C steps
DATABASE = 'TCOX14'
ELEMENTS = ['Cu', 'Al', 'O']

# Composition: roughly stoichiometric for Cu + Al2O3 interface
# Cu: 0.2, Al: 0.32, O: 0.48 (Al2O3 is 40% Al, 60% O)
COMPOSITIONS = {
    'X(Al)': 0.32,
    'X(O)': 0.48
    # X(Cu) = 1 - X(Al) - X(O) = 0.2
}


def main():
    print(f"TC-Python Cu-Al-O Phase Stability Calculation")
    print(f"=" * 50)
    print(f"Database: {DATABASE}")
    print(f"Elements: {ELEMENTS}")
    print(f"Temperature range: {min(TEMPERATURES_C)}-{max(TEMPERATURES_C)}°C")
    print(f"Output: {OUTPUT_FILE}")
    print()

    results = []

    with TCPython() as session:
        print("Setting up system...")
        system = session.select_database_and_elements(DATABASE, ELEMENTS)
        calc = system.with_single_equilibrium_calculation()

        # Set fixed conditions
        calc.set_condition('P', 101325)  # 1 atm in Pa
        for element, value in COMPOSITIONS.items():
            calc.set_condition(element, value)

        print(f"Running {len(list(TEMPERATURES_C))} calculations...")
        print()

        for T_C in TEMPERATURES_C:
            T_K = T_C + 273.15
            calc.set_condition('T', T_K)

            try:
                result = calc.calculate()
                phases = result.get_stable_phases()

                row = {
                    'T_C': T_C,
                    'T_K': T_K,
                    'phases': '; '.join(phases),
                    'num_phases': len(phases),
                    'has_CuAlO2': 'CUALUMINATE' in str(phases).upper() or 'CUALOXID' in str(phases).upper(),
                    'has_spinel': 'SPINEL' in str(phases).upper(),
                    'has_corundum': 'CORUNDUM' in str(phases).upper() or 'AL2O3' in str(phases).upper(),
                }
                results.append(row)
                print(f"  {T_C}°C: {phases}")

            except Exception as e:
                print(f"  {T_C}°C: ERROR - {e}")
                results.append({
                    'T_C': T_C,
                    'T_K': T_K,
                    'phases': f'ERROR: {e}',
                    'num_phases': 0,
                    'has_CuAlO2': False,
                    'has_spinel': False,
                    'has_corundum': False,
                })

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write CSV
    fieldnames = ['T_C', 'T_K', 'phases', 'num_phases', 'has_CuAlO2', 'has_spinel', 'has_corundum']
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Timestamp: {datetime.now().isoformat()}")


if __name__ == '__main__':
    main()
