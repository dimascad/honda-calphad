"""
Interactive label picker for dG vs T plot.

Click on the plot to place each label. Press Backspace to undo last placement.
After all labels are placed, the final figure is saved.

Usage: python3 label_picker_dG.py
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # interactive backend
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "dG_vs_T_top6.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

PRODUCT_ORDER = [
    "CuFe2O4", "Cu3V2O8", "CuMn2O4", "Cu2SiO4", "CuB2O4", "CuAl2O4",
]

SHORT_LABELS = {
    "CuFe2O4": r"CuFe$_2$O$_4$",
    "Cu3V2O8": r"Cu$_3$V$_2$O$_8$",
    "CuMn2O4": r"CuMn$_2$O$_4$",
    "Cu2SiO4": r"Cu$_2$SiO$_4$",
    "CuB2O4":  r"CuB$_2$O$_4$",
    "CuAl2O4": r"CuAl$_2$O$_4$",
}

COLORS = {
    "CuFe2O4": "#0077BB",
    "Cu3V2O8": "#EE7733",
    "CuMn2O4": "#AA3377",
    "Cu2SiO4": "#009988",
    "CuB2O4":  "#EE3377",
    "CuAl2O4": "#BBBBBB",
}

LINE_STYLES = {
    "CuFe2O4": "-",
    "Cu3V2O8": "--",
    "CuMn2O4": ":",
    "Cu2SiO4": "-.",
    "CuB2O4":  "-",
    "CuAl2O4": "--",
}

MARKERS = {
    "CuFe2O4": "o",
    "Cu3V2O8": "s",
    "CuMn2O4": "^",
    "Cu2SiO4": "D",
    "CuB2O4":  "v",
    "CuAl2O4": "P",
}


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def extract_dG_vs_T(rows, product):
    T_vals, dG_vals = [], []
    for r in rows:
        if r["product"] != product:
            continue
        try:
            T = float(r["T_K"])
            dG = float(r["dG_rxn_system_kJ"])
            T_vals.append(T)
            dG_vals.append(dG)
        except (ValueError, KeyError):
            pass
    return np.array(T_vals), np.array(dG_vals)


def build_base_plot(rows):
    """Create the base plot without labels. Returns fig, ax, line_data."""
    fig, ax = plt.subplots(figsize=(10, 6))
    line_data = {}

    for product in PRODUCT_ORDER:
        T_arr, dG_arr = extract_dG_vs_T(rows, product)
        if len(T_arr) == 0:
            continue
        order = np.argsort(T_arr)
        T_arr = T_arr[order]
        dG_arr = dG_arr[order]
        T_C = T_arr - 273.15

        ax.plot(T_C, dG_arr,
                color=COLORS[product],
                linestyle=LINE_STYLES[product],
                marker=MARKERS[product],
                markersize=4, markevery=3,
                linewidth=1.8)
        line_data[product] = (T_C, dG_arr)

    ax.axhline(y=0, color='black', linewidth=0.8, linestyle='-', alpha=0.5)
    ax.axvspan(1500, 1650, color='#CCCCCC', alpha=0.25, zorder=0)
    ax.text(1575, 5, "Steelmaking\nrange", fontsize=8, color='#777777',
            ha='center', va='bottom', style='italic')

    ax.set_xlabel("Temperature (C)", fontsize=12)
    ax.set_ylabel(r"$\Delta G_{rxn}$ (kJ/mol)", fontsize=12)
    ax.set_title(r"Reaction Free Energy: Cu + MO$_x$ + O$_2$ $\rightarrow$ CuMO$_y$",
                 fontsize=13)
    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    return fig, ax, line_data


def main():
    rows = load_csv(CSV_IN)
    fig, ax, line_data = build_base_plot(rows)

    # State for interactive placement
    labels_to_place = list(PRODUCT_ORDER)
    placed_labels = []  # list of (product, annotation_object)
    current_idx = [0]

    def get_current():
        if current_idx[0] < len(labels_to_place):
            return labels_to_place[current_idx[0]]
        return None

    def update_title():
        product = get_current()
        if product:
            fig.suptitle(
                f"Click to place: {SHORT_LABELS[product]}  "
                f"({current_idx[0]+1}/{len(labels_to_place)})  |  Backspace = undo",
                fontsize=10, color=COLORS[product], fontweight='bold', y=0.98)
        else:
            fig.suptitle("All labels placed! Close window to save.",
                         fontsize=10, color='green', fontweight='bold', y=0.98)
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax:
            return
        product = get_current()
        if product is None:
            return

        ann = ax.annotate(
            SHORT_LABELS[product],
            xy=(event.xdata, event.ydata),
            fontsize=6.5, fontweight='bold',
            color=COLORS[product],
            ha='center', va='center',
        )
        placed_labels.append((product, ann))
        current_idx[0] += 1
        update_title()

    def on_key(event):
        if event.key == 'backspace' and placed_labels:
            product, ann = placed_labels.pop()
            ann.remove()
            current_idx[0] -= 1
            update_title()

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)

    update_title()
    print("=" * 60)
    print("LABEL PICKER — dG vs T")
    print("=" * 60)
    print("  Click to place each label (centered on click)")
    print("  Backspace to undo last placement")
    print("  Close window when done to save")
    print("=" * 60)
    plt.show()

    # After window closes, save with labels
    if placed_labels:
        # Rebuild the plot with the placed label positions
        fig2, ax2, _ = build_base_plot(rows)
        for product, ann in placed_labels:
            x, y = ann.xy
            ax2.annotate(
                SHORT_LABELS[product],
                xy=(x, y),
                fontsize=6.5, fontweight='bold',
                color=COLORS[product],
                ha='center', va='center',
            )

        FIG_DIR.mkdir(parents=True, exist_ok=True)
        png_path = FIG_DIR / "dG_vs_T_top6.png"
        pdf_path = FIG_DIR / "dG_vs_T_top6.pdf"
        fig2.savefig(png_path, dpi=300, bbox_inches='tight')
        fig2.savefig(pdf_path, bbox_inches='tight')
        plt.close(fig2)
        print(f"\nSaved: {png_path}")
        print(f"Saved: {pdf_path}")
    else:
        print("\nNo labels placed. Figures not saved.")


if __name__ == "__main__":
    main()
