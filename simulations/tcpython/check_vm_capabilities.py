#!/usr/bin/env python3
"""
Check what databases, modules, and capabilities are available on the OSU VM.

This is a diagnostic script — it does NOT do calculations.
It probes for:
  1. Thermodynamic databases (TCOX14, TCFE12/13, SSUB3+, etc.)
  2. Mobility databases (MOBFE5-9, MOBOX if it exists, MOBCU)
  3. Combined database loading (TCFE + TCOX together)
  4. DICTRA diffusion module availability
  5. Process Metallurgy Module availability

Results are printed to the terminal AND saved to a text file for easy copy.

Run on OSU lab machine:
  "C:\\Program Files\\Thermo-Calc\\2025b\\python\\python.exe" check_vm_capabilities.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Output file — save next to this script
SCRIPT_DIR = Path(__file__).parent
OUT_FILE = SCRIPT_DIR / "vm_capabilities_report.txt"

# All databases to probe
THERMO_DBS = [
    "TCOX14", "TCOX13", "TCOX12", "TCOX11", "TCOX10", "TCOX9",
    "TCFE13", "TCFE12", "TCFE11", "TCFE10",
    "SSUB6", "SSUB5", "SSUB4", "SSUB3",
    "TCAL8", "TCAL7", "TCAL6",
    "TCCU4", "TCCU3", "TCCU2",
]

MOBILITY_DBS = [
    "MOBFE9", "MOBFE8", "MOBFE7", "MOBFE6", "MOBFE5",
    "MOBOX1", "MOBOX2",  # oxide mobility — probably doesn't exist
    "MOBCU3", "MOBCU2", "MOBCU1",
    "MOBNI5", "MOBNI4", "MOBNI3",
    "MOBAL2", "MOBAL1",
]


def log(msg, lines):
    """Print and accumulate output."""
    print(msg)
    lines.append(msg)


def check_single_db(session, db_name, lines):
    """Try to select a database. Returns True if it exists."""
    try:
        calc = session.select_database_and_elements(db_name, [])
        log("    [FOUND]  %s" % db_name, lines)
        return True
    except Exception as e:
        err = str(e)
        if "not found" in err.lower() or "does not exist" in err.lower() or "cannot" in err.lower():
            log("    [-----]  %s" % db_name, lines)
        else:
            log("    [ERROR]  %s — %s" % (db_name, err[:80]), lines)
        return False


def check_combined_databases(session, lines):
    """Try loading TCFE + TCOX together (needed for metallic + oxide phases)."""
    log("", lines)
    log("=" * 60, lines)
    log("3. COMBINED DATABASE LOADING", lines)
    log("=" * 60, lines)

    combos = [
        ("TCFE + TCOX", ["TCFE13", "TCOX14"]),
        ("TCFE + TCOX (older)", ["TCFE12", "TCOX14"]),
        ("TCFE + TCOX (oldest)", ["TCFE11", "TCOX13"]),
    ]

    for label, dbs in combos:
        try:
            # Try selecting both databases with Cu, Fe, O elements
            calc = session.select_database_and_elements(dbs[0], ["CU", "FE", "O"])
            # Add second database
            calc = calc.select_database_and_elements(dbs[1], ["CU", "FE", "O"])
            log("    [OK]     %s — loaded together" % label, lines)

            # Try to get phases from combined system
            try:
                system = calc.get_system()
                phases = system.get_phase_names()
                log("             Phases available: %d" % len(phases), lines)
                # Check for key phases
                has_fcc = any("FCC" in p for p in phases)
                has_ionic = any("IONIC" in p for p in phases)
                has_spinel = any("SPINEL" in p for p in phases)
                log("             FCC_A1 (metallic): %s" % ("YES" if has_fcc else "no"), lines)
                log("             IONIC_LIQ (slag):  %s" % ("YES" if has_ionic else "no"), lines)
                log("             SPINEL:            %s" % ("YES" if has_spinel else "no"), lines)
            except Exception as e2:
                log("             (could not enumerate phases: %s)" % str(e2)[:60], lines)

        except Exception as e:
            err = str(e)[:100]
            if "not found" in err.lower() or "does not exist" in err.lower():
                log("    [MISS]   %s — one or both not installed" % label, lines)
            elif "conflict" in err.lower() or "incompatible" in err.lower():
                log("    [CLASH]  %s — databases conflict: %s" % (label, err), lines)
            else:
                log("    [ERROR]  %s — %s" % (label, err), lines)


def check_dictra(session, lines):
    """Check if DICTRA module is available."""
    log("", lines)
    log("=" * 60, lines)
    log("4. DICTRA / DIFFUSION MODULE", lines)
    log("=" * 60, lines)

    # Method 1: Try creating a diffusion calculation
    try:
        calc = (session
                .select_thermodynamic_and_kinetic_databases_with_elements(
                    "TCFE13", "MOBFE9", ["CU", "FE"])
                .get_system()
                .with_diffusion_calculation())
        log("    [OK]     DICTRA available (TCFE13 + MOBFE9)", lines)
        return
    except Exception as e:
        err = str(e)

    # Method 2: Try older versions
    for tdb, mob in [("TCFE12", "MOBFE8"), ("TCFE12", "MOBFE7"),
                     ("TCFE11", "MOBFE6"), ("TCFE10", "MOBFE5")]:
        try:
            calc = (session
                    .select_thermodynamic_and_kinetic_databases_with_elements(
                        tdb, mob, ["CU", "FE"])
                    .get_system()
                    .with_diffusion_calculation())
            log("    [OK]     DICTRA available (%s + %s)" % (tdb, mob), lines)
            return
        except Exception:
            pass

    # Method 3: Check if the API method even exists
    if hasattr(session, 'select_thermodynamic_and_kinetic_databases_with_elements'):
        log("    [AVAIL]  DICTRA API exists but no compatible DB pair found", lines)
        log("             (need both TCFE + MOBFE installed)", lines)
    else:
        log("    [NONE]   DICTRA API not available in this TC-Python version", lines)


def check_process_metallurgy(session, lines):
    """Check if Process Metallurgy Module is available."""
    log("", lines)
    log("=" * 60, lines)
    log("5. PROCESS METALLURGY MODULE", lines)
    log("=" * 60, lines)

    try:
        # Try accessing the process metallurgy API
        if hasattr(session, 'with_process_metallurgy_calculation'):
            log("    [AVAIL]  Process Metallurgy API found on session object", lines)
        else:
            log("    [NONE]   No process metallurgy API on session object", lines)
    except Exception as e:
        log("    [ERROR]  %s" % str(e)[:80], lines)

    # Also check if PropertyModel module exists
    try:
        if hasattr(session, 'with_property_model_calculation'):
            log("    [AVAIL]  Property Model API found", lines)
        else:
            log("    [-----]  No Property Model API on session object", lines)
    except Exception:
        pass


def main():
    lines = []

    log("=" * 60, lines)
    log("TC-PYTHON VM CAPABILITIES REPORT", lines)
    log("Date: %s" % datetime.now().strftime("%Y-%m-%d %H:%M"), lines)
    log("=" * 60, lines)

    # Import TC-Python
    try:
        from tc_python import TCPython
        log("TC-Python imported successfully.", lines)
    except ImportError as e:
        log("FATAL: Cannot import tc_python — %s" % str(e), lines)
        log("Make sure you run with the TC-Python bundled Python.", lines)
        with open(OUT_FILE, "w") as f:
            f.write("\n".join(lines))
        return

    with TCPython() as session:
        # --- 1. Thermodynamic databases ---
        log("", lines)
        log("=" * 60, lines)
        log("1. THERMODYNAMIC DATABASES", lines)
        log("=" * 60, lines)

        found_thermo = []
        for db in THERMO_DBS:
            if check_single_db(session, db, lines):
                found_thermo.append(db)

        # --- 2. Mobility databases ---
        log("", lines)
        log("=" * 60, lines)
        log("2. MOBILITY / KINETIC DATABASES", lines)
        log("=" * 60, lines)

        found_mobility = []
        for db in MOBILITY_DBS:
            if check_single_db(session, db, lines):
                found_mobility.append(db)

        # --- 3. Combined database loading ---
        check_combined_databases(session, lines)

        # --- 4. DICTRA ---
        check_dictra(session, lines)

        # --- 5. Process Metallurgy ---
        check_process_metallurgy(session, lines)

    # --- Summary ---
    log("", lines)
    log("=" * 60, lines)
    log("SUMMARY", lines)
    log("=" * 60, lines)
    log("Thermodynamic DBs found: %s" % ", ".join(found_thermo) if found_thermo else "  (none)", lines)
    log("Mobility DBs found:      %s" % ", ".join(found_mobility) if found_mobility else "  (none)", lines)
    log("", lines)

    # Recommendations based on findings
    log("RECOMMENDATIONS FOR CAPSTONE:", lines)
    if any("TCFE" in db for db in found_thermo):
        tcfe = [db for db in found_thermo if "TCFE" in db][0]
        log("  - Re-run Script 2 (cu_activity) with %s + TCOX14" % tcfe, lines)
        log("    This adds FCC_A1 (metallic Cu/Fe) alongside IONIC_LIQ (slag)", lines)
        log("    → should show a_Cu dropping as oxide fraction increases", lines)
    else:
        log("  - No TCFE database found. Cannot model metallic + oxide together.", lines)

    if any("MOBFE" in db for db in found_mobility):
        mobfe = [db for db in found_mobility if "MOBFE" in db][0]
        log("  - Cu diffusion in steel phase possible with %s" % mobfe, lines)
        log("    But NO oxide mobility DB exists → no DICTRA in slag/spinel", lines)
    else:
        log("  - No mobility databases found. DICTRA not available.", lines)

    log("", lines)
    log("Report saved to: %s" % OUT_FILE, lines)

    # Save to file
    with open(OUT_FILE, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
