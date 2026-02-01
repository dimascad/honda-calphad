"""
Process Thermo-Calc exports for plotting.
Run from the data/ directory.
"""

import pandas as pd
from pathlib import Path

RAW = Path("thermocalc/raw")
OUT = Path("thermocalc/processed")
OUT.mkdir(exist_ok=True)


def process_oxide(filename, o2_factor):
    """
    Convert Thermo-Calc GM output to dGf per mol O2 for Ellingham diagram.

    Parameters:
        filename: name of raw TC export file
        o2_factor: moles of O2 in formation reaction (0.5 for Cu2O, 1.5 for Al2O3, etc.)
    """
    filepath = RAW / filename
    if not filepath.exists():
        print(f"Skipping {filename} (not found)")
        return

    # Read TC export (tab-separated)
    df = pd.read_csv(filepath, sep='\t', comment='#')

    # Standardize column names
    df.columns = [c.strip() for c in df.columns]

    # Find temperature and Gibbs energy columns
    t_col = [c for c in df.columns if 'T' in c.upper()][0]
    g_col = [c for c in df.columns if 'G' in c.upper()][0]

    # Create processed dataframe
    out = pd.DataFrame()
    out['T_K'] = df[t_col]
    out['T_C'] = out['T_K'] - 273.15
    out['GM_J'] = df[g_col]
    out['GM_kJ'] = out['GM_J'] / 1000
    out['dGf_kJ_per_molO2'] = out['GM_kJ'] / o2_factor

    # Save
    out_name = filename.replace('.txt', '_processed.csv')
    out.to_csv(OUT / out_name, index=False)
    print(f"Processed: {filename} -> {out_name}")


def process_activity(filename):
    """Process Cu activity data."""
    filepath = RAW / filename
    if not filepath.exists():
        print(f"Skipping {filename} (not found)")
        return

    df = pd.read_csv(filepath, sep='\t', comment='#')
    df.columns = [c.strip() for c in df.columns]

    out_name = filename.replace('.txt', '_processed.csv')
    df.to_csv(OUT / out_name, index=False)
    print(f"Processed: {filename} -> {out_name}")


if __name__ == "__main__":
    print("Processing oxide Gibbs energy data...")
    print("-" * 40)

    # Oxide files and their O2 factors
    oxides = [
        ('cu2o_dGf_1273-1873K.txt', 0.5),
        ('cuo_dGf_1273-1873K.txt', 0.5),
        ('al2o3_dGf_1273-1873K.txt', 1.5),
        ('mgo_dGf_1273-1873K.txt', 0.5),
        ('sio2_dGf_1273-1873K.txt', 1.0),
        ('tio2_dGf_1273-1873K.txt', 1.0),
        ('feo_dGf_1273-1873K.txt', 0.5),
    ]

    for filename, o2_factor in oxides:
        process_oxide(filename, o2_factor)

    print("\nProcessing activity data...")
    print("-" * 40)

    activity_files = [
        'fe-cu_activity-vs-xcu_1873K.txt',
        'fe-cu_activity-vs-T_xcu003.txt',
    ]

    for filename in activity_files:
        process_activity(filename)

    print("\nDone!")
