#!/usr/bin/env python3
"""
Diagnostic script: Check available TC databases and phases.
Run this FIRST to see what's available on the lab machine.

Run on OSU lab machine:
    "C:\Program Files\Thermo-Calc\2025b\python\python.exe" check_databases.py
"""

try:
    from tc_python import *
except ImportError:
    print("ERROR: tc_python not found. Run this on OSU lab machine.")
    exit(1)

print("=" * 70)
print("TC-Python Database Diagnostic")
print("=" * 70)

with TCPython() as session:
    # List all databases
    databases = session.get_databases()
    print(f"\nAvailable databases ({len(databases)} total):")
    for db in sorted(databases):
        print(f"  {db}")

    # Check specific databases we care about
    target_dbs = ["SSUB6", "SSUB5", "SSUB3", "TCOX14", "TCOX12", "TCFE14", "TCCU6"]
    print(f"\n{'=' * 70}")
    print("Databases of interest:")
    for db in target_dbs:
        status = "AVAILABLE" if db in databases else "NOT FOUND"
        print(f"  {db}: {status}")

    # Try to list phases in a pure substance database
    print(f"\n{'=' * 70}")
    for db in ["SSUB6", "SSUB5", "SSUB3"]:
        if db in databases:
            print(f"\nPhases in {db} for Cu-O system:")
            try:
                system = session.select_database_and_elements(db, ["CU", "O"]).get_system()
                phases = system.get_phase_names()
                for p in phases:
                    print(f"  {p}")
            except Exception as e:
                print(f"  Error: {e}")
            break

    # Check TCOX if available
    for db in ["TCOX14", "TCOX12", "TCOX10"]:
        if db in databases:
            print(f"\n{'=' * 70}")
            print(f"Phases in {db} for Cu-Al-O system:")
            try:
                system = session.select_database_and_elements(db, ["CU", "AL", "O"]).get_system()
                phases = system.get_phase_names()
                for p in phases:
                    print(f"  {p}")
            except Exception as e:
                print(f"  Error: {e}")
            break

print(f"\n{'=' * 70}")
print("Diagnostic complete. Copy this output and share it.")
print("=" * 70)
