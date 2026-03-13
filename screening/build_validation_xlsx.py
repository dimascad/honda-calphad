"""
Compile all validation data into one Excel workbook.

Reads all 5 CSV outputs and builds a multi-sheet workbook:
  Sheet 1: CuFe2O4 Decomposition (Script 1 results)
  Sheet 2: Cu Activity vs Oxide (Script 2 results)
  Sheet 3: dG vs T Top 6 (Script 3 results)
  Sheet 4: Phase Map Summary (Script 4 phase counts)
  Sheet 5: Slag Basicity Effects (Script 5 results)
  Sheet 6: Verification Notes

Run locally after all post-processing is complete.
"""

import csv
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "tcpython" / "raw"
OUTPUT_FILE = SCRIPT_DIR / "Validation_Results.xlsx"

# Input CSVs
CSV_FILES = {
    "cufe2o4": DATA_DIR / "cufe2o4_alternative_reaction.csv",
    "activity": DATA_DIR / "cu_activity_vs_oxide.csv",
    "dG_top6": DATA_DIR / "dG_vs_T_top6.csv",
    "phase_map": DATA_DIR / "ternary_phase_map_1800K.csv",
    "slag": DATA_DIR / "slag_composition_effects.csv",
}

# IEEE table formatting per CLAUDE.md
HEADER_FILL = PatternFill(start_color="595959", end_color="595959", fill_type="solid") if HAS_OPENPYXL else None
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10) if HAS_OPENPYXL else None
WHITE_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid") if HAS_OPENPYXL else None
GRAY_FILL = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid") if HAS_OPENPYXL else None

if HAS_OPENPYXL:
    THICK_SIDE = Side(style='medium')
    THIN_SIDE = Side(style='thin')


def load_csv(path):
    """Load CSV and return (fieldnames, rows)."""
    if not path.exists():
        return None, []
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames if hasattr(reader, 'fieldnames') else (list(rows[0].keys()) if rows else []), rows
    # Re-read to get fieldnames properly
    with open(path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return fieldnames, rows


def load_csv_proper(path):
    """Load CSV returning fieldnames and rows."""
    if not path.exists():
        return None, []
    with open(path) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return fieldnames, rows


def style_header(ws, row_num, num_cols):
    """Apply IEEE header styling to a row."""
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)


def style_data_rows(ws, start_row, end_row, num_cols, group_size=1):
    """Apply alternating group shading."""
    for row_num in range(start_row, end_row + 1):
        group_idx = (row_num - start_row) // group_size
        fill = WHITE_FILL if group_idx % 2 == 0 else GRAY_FILL
        for col in range(1, num_cols + 1):
            cell = ws.cell(row=row_num, column=col)
            cell.fill = fill
            cell.alignment = Alignment(horizontal='center')
            # Try to convert numeric strings
            try:
                val = float(cell.value)
                cell.value = val
                cell.number_format = '+0.0;-0.0;0.0' if 'dG' in str(ws.cell(row=1, column=col).value) else '0.000'
            except (TypeError, ValueError):
                pass


def auto_width(ws, num_cols):
    """Auto-fit column widths."""
    for col in range(1, num_cols + 1):
        max_len = 0
        for row in ws.iter_rows(min_col=col, max_col=col, values_only=False):
            for cell in row:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[get_column_letter(col)].width = min(max_len + 3, 30)


def write_csv_to_sheet(ws, fieldnames, rows, sheet_title=None, group_size=1):
    """Write CSV data to a worksheet with IEEE formatting."""
    if sheet_title:
        ws.title = sheet_title

    # Header row
    for col, name in enumerate(fieldnames, 1):
        ws.cell(row=1, column=col, value=name)
    style_header(ws, 1, len(fieldnames))

    # Data rows
    for row_idx, row_data in enumerate(rows, 2):
        for col, name in enumerate(fieldnames, 1):
            ws.cell(row=row_idx, column=col, value=row_data.get(name, ""))

    style_data_rows(ws, 2, len(rows) + 1, len(fieldnames), group_size)
    auto_width(ws, len(fieldnames))


def main():
    if not HAS_OPENPYXL:
        print("ERROR: openpyxl not installed.")
        print("Install with: pip install openpyxl")
        return

    print("=" * 70)
    print("Building Validation Results Workbook")
    print("=" * 70)

    wb = openpyxl.Workbook()

    # =====================================================================
    # Sheet 1: CuFe2O4 Decomposition
    # =====================================================================
    fieldnames, rows = load_csv_proper(CSV_FILES["cufe2o4"])
    ws = wb.active
    if fieldnames and rows:
        write_csv_to_sheet(ws, fieldnames, rows, "CuFe2O4 Decomposition")
        print(f"  Sheet 1: CuFe2O4 Decomposition ({len(rows)} rows)")
    else:
        ws.title = "CuFe2O4 Decomposition"
        ws.cell(row=1, column=1, value="Data not yet available")
        print("  Sheet 1: CuFe2O4 Decomposition (no data)")

    # =====================================================================
    # Sheet 2: Cu Activity vs Oxide
    # =====================================================================
    fieldnames, rows = load_csv_proper(CSV_FILES["activity"])
    ws = wb.create_sheet()
    if fieldnames and rows:
        write_csv_to_sheet(ws, fieldnames, rows, "Cu Activity", group_size=20)
        print(f"  Sheet 2: Cu Activity ({len(rows)} rows)")
    else:
        ws.title = "Cu Activity"
        ws.cell(row=1, column=1, value="Data not yet available")
        print("  Sheet 2: Cu Activity (no data)")

    # =====================================================================
    # Sheet 3: dG vs T Top 6
    # =====================================================================
    fieldnames, rows = load_csv_proper(CSV_FILES["dG_top6"])
    ws = wb.create_sheet()
    if fieldnames and rows:
        write_csv_to_sheet(ws, fieldnames, rows, "dG vs T Top 6", group_size=45)
        print(f"  Sheet 3: dG vs T Top 6 ({len(rows)} rows)")
    else:
        ws.title = "dG vs T Top 6"
        ws.cell(row=1, column=1, value="Data not yet available")
        print("  Sheet 3: dG vs T Top 6 (no data)")

    # =====================================================================
    # Sheet 4: Phase Map Summary
    # =====================================================================
    fieldnames, rows = load_csv_proper(CSV_FILES["phase_map"])
    ws = wb.create_sheet()
    if fieldnames and rows:
        # Summarize: count dominant phases per system
        ws.title = "Phase Map 1800K"
        summary_rows = []
        systems = {}
        for r in rows:
            sys_name = r.get("system", "")
            dominant = r.get("dominant_phase", "")
            if not dominant or "ERROR" in r.get("stable_phases", ""):
                continue
            if sys_name not in systems:
                systems[sys_name] = {}
            systems[sys_name][dominant] = systems[sys_name].get(dominant, 0) + 1

        # Write summary table
        sum_fields = ["System", "Phase", "Count", "Percentage"]
        for col, name in enumerate(sum_fields, 1):
            ws.cell(row=1, column=col, value=name)
        style_header(ws, 1, len(sum_fields))

        row_num = 2
        for sys_name, phase_counts in systems.items():
            total = sum(phase_counts.values())
            for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
                pct = f"{100.0 * count / total:.1f}%"
                ws.cell(row=row_num, column=1, value=sys_name)
                ws.cell(row=row_num, column=2, value=phase)
                ws.cell(row=row_num, column=3, value=count)
                ws.cell(row=row_num, column=4, value=pct)
                row_num += 1

        style_data_rows(ws, 2, row_num - 1, len(sum_fields))
        auto_width(ws, len(sum_fields))

        # Also add raw data on a separate sheet
        ws_raw = wb.create_sheet("Phase Map Raw")
        write_csv_to_sheet(ws_raw, fieldnames, rows, "Phase Map Raw")

        print(f"  Sheet 4: Phase Map 1800K (summary + {len(rows)} raw rows)")
    else:
        ws.title = "Phase Map 1800K"
        ws.cell(row=1, column=1, value="Data not yet available")
        print("  Sheet 4: Phase Map 1800K (no data)")

    # =====================================================================
    # Sheet 5: Slag Basicity Effects
    # =====================================================================
    fieldnames, rows = load_csv_proper(CSV_FILES["slag"])
    ws = wb.create_sheet()
    if fieldnames and rows:
        write_csv_to_sheet(ws, fieldnames, rows, "Slag Effects", group_size=15)
        print(f"  Sheet 5: Slag Effects ({len(rows)} rows)")
    else:
        ws.title = "Slag Effects"
        ws.cell(row=1, column=1, value="Data not yet available")
        print("  Sheet 5: Slag Effects (no data)")

    # =====================================================================
    # Sheet 6: Verification Notes
    # =====================================================================
    ws = wb.create_sheet("Verification Notes")
    notes = [
        ["Check", "Criterion", "Status"],
        ["Script 3 vs existing", "dG values match at 50K steps (within 1 kJ)", "Run plot_dG_vs_T.py to verify"],
        ["Script 1 alternative dG", "Less negative than -112 kJ, closer to CuAl2O4 (-32 kJ)", "Check CuFe2O4 Decomposition sheet"],
        ["Script 2 a_Cu", "~1.0 at high X_Cu, drops as oxide increases", "Check Cu Activity sheet"],
        ["Script 4 phases", "IONIC_LIQ dominates at 1800K", "Check Phase Map sheet"],
        ["Script 5 trends", "a_Cu monotonic or smooth vs basicity", "Check Slag Effects sheet"],
    ]
    for row_idx, row_data in enumerate(notes):
        for col_idx, val in enumerate(row_data):
            ws.cell(row=row_idx + 1, column=col_idx + 1, value=val)
    style_header(ws, 1, 3)
    auto_width(ws, 3)
    print("  Sheet 6: Verification Notes")

    # Save
    wb.save(OUTPUT_FILE)
    print(f"\nWorkbook saved to: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
