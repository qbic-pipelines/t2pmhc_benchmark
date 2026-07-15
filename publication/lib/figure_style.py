"""Figure styling + sizing helpers shared by the publication notebooks.

    import sys
    sys.path.insert(0, str(PUB / "lib"))
    from figure_style import apply_style, figsize, add_panel_labels, save_figure

    flierprops = apply_style()
    fig, axes = plt.subplots(1, 2, figsize=figsize("double", 90))
    ...
    save_figure(fig, "my_figure", subdir="fig5")
"""

from __future__ import annotations

import locale
import string
from pathlib import Path

# Column widths (mm) and raster settings used by figsize()/save_figure().
COL_SINGLE_MM = 86.0
COL_DOUBLE_MM = 178.0
MM_PER_IN = 25.4
DPI = 350
FONT_MIN_PT = 12

# Default output root: publication/figures/ (this file is publication/lib/figure_style.py).
FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"


def apply_style():
    """Set matplotlib + seaborn rcParams: editable-SVG text, white background, 350 dpi,
    >=12 pt fonts, no gridlines. Returns the boxplot flierprops dict."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Keep text editable in SVG output (do not convert glyphs to paths).
    plt.rcParams.update({"text.usetex": False, "svg.fonttype": "none"})
    sns.set_context("paper")
    sns.set_style("white", {"xtick.bottom": True, "ytick.left": True})
    # US-style thousands separators (1,000 not 1000) when available.
    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        plt.rcParams["axes.formatter.use_locale"] = True
    except locale.Error:
        plt.rcParams["axes.formatter.use_locale"] = False

    plt.rcParams["figure.dpi"] = DPI
    plt.rcParams["savefig.dpi"] = DPI

    # Font sizes set after set_context (which would otherwise shrink them).
    plt.rcParams.update({
        "font.size": 12,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 12,
        "font.weight": "normal",
        "axes.labelweight": "normal",
        "axes.titleweight": "normal",
        "axes.grid": False,
    })

    flierprops = dict(
        marker="d", markerfacecolor="black", markersize=2, markeredgecolor="black"
    )
    return flierprops


def figsize(width="single", height_mm=None):
    """Return ``(width_in, height_in)`` for a given column width.

    ``width`` is "single" (86 mm), "double" (178 mm), or a custom width in mm.
    ``height_mm`` defaults to ~0.66 of the width.
    """
    if isinstance(width, str):
        key = width.lower()
        if key == "single":
            width_mm = COL_SINGLE_MM
        elif key == "double":
            width_mm = COL_DOUBLE_MM
        else:
            raise ValueError(f"width must be 'single', 'double', or a number; got {width!r}")
    else:
        width_mm = float(width)

    if height_mm is None:
        height_mm = width_mm * 0.66
    return (width_mm / MM_PER_IN, height_mm / MM_PER_IN)


def _flatten_axes(axes):
    """Normalise an Axes / ndarray / iterable of Axes to a flat list of Axes."""
    try:
        return list(axes.ravel())
    except AttributeError:
        if hasattr(axes, "text"):
            return [axes]
        return list(axes)


def _y_tick_step(ax):
    """Median spacing of the axis' current y major ticks, or None if undeterminable."""
    ticks = list(ax.get_yticks())
    diffs = sorted(b - a for a, b in zip(ticks, ticks[1:]) if b - a > 0)
    if not diffs:
        return None
    return diffs[len(diffs) // 2]


def set_y_headroom(axes, frac=0.05, snap_to_ticks=True):
    """Raise each axis' top y-limit so the data clears the top spine, optionally rounding
    up to the next major-tick multiple. Bottom limit and log axes' snapping are left as-is.

    ``frac`` is the minimal fractional clearance above the data max before snapping.
    """
    import math

    for ax in _flatten_axes(axes):
        data_top = ax.dataLim.ymax
        data_bottom = ax.dataLim.ymin
        if not (math.isfinite(data_top) and math.isfinite(data_bottom)):
            continue
        bottom, top = ax.get_ylim()
        is_log = ax.get_yscale() == "log"
        if is_log:
            required_top = data_top * (1.0 + frac)
        else:
            span = data_top - data_bottom
            pad = frac * span if span > 0 else frac * abs(data_top) or frac
            required_top = data_top + pad
            if snap_to_ticks:
                step = _y_tick_step(ax)
                if step:
                    # Round up to the next gridline; subtract eps so an exact multiple is kept.
                    required_top = math.ceil(required_top / step - 1e-9) * step
        new_top = max(top, required_top) if top >= bottom else required_top
        ax.set_ylim(bottom, new_top)


def add_panel_labels(axes, labels=None, fontsize=16, x=-0.1, y=1.05, fontweight="normal"):
    """Add panel labels (a, b, c, ...) to the upper-left of each subplot. A 2D ndarray of
    axes is flattened row-major. ``labels`` defaults to lowercase letters."""
    flat = _flatten_axes(axes)
    if labels is None:
        labels = list(string.ascii_lowercase[: len(flat)])

    for ax, label in zip(flat, labels):
        ax.text(x, y, label, transform=ax.transAxes,
                fontsize=fontsize, fontweight=fontweight, va="top", ha="right")


def save_figure(fig, name, subdir, formats=("svg", "png"), base=FIGURES_DIR, tight=False):
    """Save ``fig`` to ``<base>/<subdir>/<name>.<ext>`` for each format (default SVG + PNG,
    both at 350 dpi). The figure is saved at its exact ``figsize`` unless ``tight=True``.
    Returns the list of files written."""
    if not subdir:
        raise ValueError("save_figure() requires a `subdir`.")
    if any(ch in name for ch in ' /\\:'):
        raise ValueError(f"Filename {name!r} must contain only letters, numbers, '-' or '_'.")

    out_dir = Path(base) / subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    save_kw = {"facecolor": "white", "dpi": DPI}
    if tight:
        save_kw["bbox_inches"] = "tight"

    written = []
    for ext in formats:
        ext = ext.lstrip(".")
        path = out_dir / f"{name}.{ext}"
        fig.savefig(path, format=ext, **save_kw)
        written.append(path)
    return written
