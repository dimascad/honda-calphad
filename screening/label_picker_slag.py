"""
Interactive label picker for slag basicity plot.

Click on the plot to place each label. Press Backspace to undo last placement.
After all labels are placed, the final figure is saved.

Usage: python3 label_picker_slag.py
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "slag_composition_effects.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

SYSTEM_ORDER = ["Cu-Mn-Si-O", "Cu-Al-Si-O"]

SHORT_LABELS = {
    "Cu-Mn-Si-O": "Cu-Mn-Si-O\n(MnO:SiO$_2$)",
    "Cu-Al-Si-O": "Cu-Al-Si-O\n(Al$_2$O$_3$:SiO$_2$)",
}

COLORS = {
    "Cu-Mn-Si-O": "#0077BB",
    "Cu-Al-Si-O": "#EE7733",
}

LINE_STYLES = {
    "Cu-Mn-Si-O": "-",
    "Cu-Al-Si-O": "--",
}

MARKERS = {
    "Cu-Mn-Si-O": "o",
    "Cu-Al-Si-O": "s",
}


def build_base_plot():
    """Create the base plot without labels. Returns fig, ax."""
    with open(CSV_IN) as f:
        rows = list(csv.DictReader(f))

    systems = {}
    for r in rows:
        sys_name = r["system"]
        if sys_name not in systems:
            systems[sys_name] = {
                "ratio": [], "a_Cu": [], "ratio_label": r["ratio_label"],
            }
        try:
            ratio = float(r["ratio_value"])
            a_Cu = float(r["a_Cu"])
            systems[sys_name]["ratio"].append(ratio)
            systems[sys_name]["a_Cu"].append(a_Cu)
        except (ValueError, KeyError):
            pass

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for sys_name in SYSTEM_ORDER:
        if sys_name not in systems:
            continue
        data = systems[sys_name]
        ratio = np.array(data["ratio"])
        a_Cu = np.array(data["a_Cu"])

        order = np.argsort(ratio)
        ratio = ratio[order]
        a_Cu = a_Cu[order]

        ax.plot(ratio, a_Cu,
                color=COLORS.get(sys_name, "#333333"),
                linestyle=LINE_STYLES.get(sys_name, "-"),
                marker=MARKERS.get(sys_name, "o"),
                markersize=6,
                linewidth=1.8)

    ax.set_xlabel("Basicity ratio (basic oxide : SiO$_2$)", fontsize=12)
    ax.set_ylabel("Cu activity (a$_{Cu}$)", fontsize=12)
    ax.set_title("Effect of Slag Basicity on Cu Activity at 1800 K\n"
                 "(X$_{Cu}$ = 0.003, steelmaking level)", fontsize=12)

    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    return fig, ax


def main():
    fig, ax = build_base_plot()

    labels_to_place = list(SYSTEM_ORDER)
    placed_labels = []
    current_idx = [0]

    def get_current():
        if current_idx[0] < len(labels_to_place):
            return labels_to_place[current_idx[0]]
        return None

    def update_title():
        sys_name = get_current()
        if sys_name:
            fig.suptitle(
                f"Click to place: {sys_name}  "
                f"({current_idx[0]+1}/{len(labels_to_place)})  |  Backspace = undo",
                fontsize=10, color=COLORS[sys_name], fontweight='bold', y=0.98)
        else:
            fig.suptitle("All labels placed! Close window to save.",
                         fontsize=10, color='green', fontweight='bold', y=0.98)
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax:
            return
        sys_name = get_current()
        if sys_name is None:
            return

        ann = ax.annotate(
            SHORT_LABELS[sys_name],
            xy=(event.xdata, event.ydata),
            fontsize=6.5, fontweight='bold',
            color=COLORS[sys_name],
            ha='center', va='center',
        )
        placed_labels.append((sys_name, ann))
        current_idx[0] += 1
        update_title()

    def on_key(event):
        if event.key == 'backspace' and placed_labels:
            sys_name, ann = placed_labels.pop()
            ann.remove()
            current_idx[0] -= 1
            update_title()

    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)

    update_title()
    print("=" * 60)
    print("LABEL PICKER — Slag Basicity")
    print("=" * 60)
    print("  Click to place each label (centered on click)")
    print("  Backspace to undo last placement")
    print("  Close window when done to save")
    print("=" * 60)
    plt.show()

    if placed_labels:
        fig2, ax2 = build_base_plot()
        for sys_name, ann in placed_labels:
            x, y = ann.xy
            ax2.annotate(
                SHORT_LABELS[sys_name],
                xy=(x, y),
                fontsize=6.5, fontweight='bold',
                color=COLORS[sys_name],
                ha='center', va='center',
            )

        FIG_DIR.mkdir(parents=True, exist_ok=True)
        png_path = FIG_DIR / "slag_basicity_vs_aCu.png"
        pdf_path = FIG_DIR / "slag_basicity_vs_aCu.pdf"
        fig2.savefig(png_path, dpi=300, bbox_inches='tight')
        fig2.savefig(pdf_path, bbox_inches='tight')
        plt.close(fig2)
        print(f"\nSaved: {png_path}")
        print(f"Saved: {pdf_path}")
    else:
        print("\nNo labels placed. Figures not saved.")


if __name__ == "__main__":
    main()
