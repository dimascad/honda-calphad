"""
Interactive label picker for Cu activity vs oxide plot.

Click on the plot to place each label. Press Backspace to undo last placement.
After all labels are placed, the final figure is saved.

Usage: python3 label_picker_activity.py
"""

import csv
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CSV_IN = SCRIPT_DIR.parent / "data" / "tcpython" / "raw" / "cu_activity_vs_oxide.csv"
FIG_DIR = SCRIPT_DIR.parent / "figures"

SYSTEM_ORDER = ["Cu-Al-O", "Cu-Mn-O", "Cu-Fe-O", "Cu-V-O"]

SHORT_LABELS = {
    "Cu-Al-O": "Cu-Al-O (Al$_2$O$_3$)",
    "Cu-Mn-O": "Cu-Mn-O (MnO)",
    "Cu-Fe-O": "Cu-Fe-O (FeO)",
    "Cu-V-O":  "Cu-V-O (V$_2$O$_5$)",
}

COLORS = {
    "Cu-Al-O": "#0077BB",
    "Cu-Mn-O": "#EE7733",
    "Cu-Fe-O": "#AA3377",
    "Cu-V-O":  "#009988",
}

LINE_STYLES = {
    "Cu-Al-O": "-",
    "Cu-Mn-O": "--",
    "Cu-Fe-O": ":",
    "Cu-V-O":  "-.",
}

MARKERS = {
    "Cu-Al-O": "o",
    "Cu-Mn-O": "s",
    "Cu-Fe-O": "^",
    "Cu-V-O":  "D",
}


def build_base_plot():
    """Create the base plot without labels. Returns fig, ax."""
    with open(CSV_IN) as f:
        rows = list(csv.DictReader(f))

    systems = {}
    for r in rows:
        sys_name = r["system"]
        if sys_name not in systems:
            systems[sys_name] = {"X_Cu": [], "a_Cu": [], "oxide": r["oxide"]}
        try:
            X_Cu = float(r["X_Cu"])
            a_Cu = float(r["a_Cu"])
            systems[sys_name]["X_Cu"].append(X_Cu)
            systems[sys_name]["a_Cu"].append(a_Cu)
        except (ValueError, KeyError):
            pass

    fig, ax = plt.subplots(figsize=(9, 5.5))

    for sys_name in SYSTEM_ORDER:
        if sys_name not in systems:
            continue
        data = systems[sys_name]
        X_Cu = np.array(data["X_Cu"])
        a_Cu = np.array(data["a_Cu"])

        X_oxide = 1 - X_Cu
        order = np.argsort(X_oxide)
        X_oxide = X_oxide[order]
        a_Cu = a_Cu[order]

        ax.plot(X_oxide, a_Cu,
                color=COLORS[sys_name],
                linestyle=LINE_STYLES[sys_name],
                marker=MARKERS[sys_name],
                markersize=5,
                linewidth=1.8)

    ax.set_xlabel("Oxide mole fraction (1 - X$_{Cu}$)", fontsize=12)
    ax.set_ylabel("Cu activity (a$_{Cu}$)", fontsize=12)
    ax.set_title("Cu Activity vs. Oxide Addition at 1800 K", fontsize=13)

    ax.set_xlim(0, 1.05)
    ax.set_ylim(bottom=0)

    ax.grid(True, which='major', alpha=0.3)
    ax.minorticks_on()
    ax.grid(True, which='minor', alpha=0.1)

    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(which='both', direction='in')

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
    print("LABEL PICKER — Cu Activity vs Oxide")
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
        png_path = FIG_DIR / "cu_activity_vs_oxide.png"
        pdf_path = FIG_DIR / "cu_activity_vs_oxide.pdf"
        fig2.savefig(png_path, dpi=300, bbox_inches='tight')
        fig2.savefig(pdf_path, bbox_inches='tight')
        plt.close(fig2)
        print(f"\nSaved: {png_path}")
        print(f"Saved: {pdf_path}")
    else:
        print("\nNo labels placed. Figures not saved.")


if __name__ == "__main__":
    main()
