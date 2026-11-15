#!/usr/bin/env python3
"""make_audit_figures.py - figures for the measurement-validity paper.

Every number plotted is read from results/*.json at draw time. Nothing is typed in. If a figure
and a results file disagree, the results file wins and this script is broken.

    .venv/bin/python figures/make_audit_figures.py

FIGURES (each written as .pdf for the paper and .png for the README)
    fig1_pipeline        the two roles a corpus plays: fitting the map, and supplying the read
                         context. A schematic; it carries no data
    fD_grid              the 8x8 fit x read factorial under `min`, with both margins     [e52, e48]
    fA_effect_and_null   (a) between-corpus z spread at four ladder rungs        [d3, cv6, cv7]
                         (b) each map against its own 15 layer-derangements      [r9]
    fB_validity          (a) where the lens is read against where the map was fitted  [cv2]
                         (b) answer rates up the ladder; (c) prompt surprisal     [cv4]
    fM_membership        32-gram containment against the readout it produces     [e48c, e52, cv3]
    fU_union             real minus deranged readout under `min`, by band width  [d1]
    fC_matching          the factorial's interaction term (not in the paper)     [e52]

STYLE. One system for every figure, so they read as a set:
  * Type is the paper's: a Times face (Times New Roman, falling back to STIX), math in STIX, sized
    for the final print width so \\includegraphics never rescales it (7-8.5 pt). PDFs embed
    TrueType (pdf.fonttype 42), never Type 3.
  * No titles inside the axes: the claim belongs in the caption. Sentence-case labels, no
    all-caps, no rotated tick labels.
  * Colour carries one meaning per encoding, everywhere. Corpus group: Pile components are blue,
    corpora from after the Pile are orange. Band summary: `min` violet, `persist` aqua. Model size
    and other ordered series: a single slate ramp, light to dark. Magnitude (the heatmap): a
    single-hue petrol ramp. Every categorical pair passes the dataviz validator (CVD and
    normal-vision separation, contrast on white); every series also carries a marker shape and a
    legend, so colour is never the only channel.

LAYOUT. Legends sit outside the axes, below their own panel: at print size, labels inside the axes
sat on the data. Figures cost page budget; unreadable figures cost more.
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OUT = HERE

# The NeurIPS 2026 style is single column with \textwidth = 5.50in. Draw at print width so
# \includegraphics never rescales the labels.
TW = 5.50

# ---- ink and surface -------------------------------------------------------------------------
INK, INK2, INK3 = "#1b1b1a", "#52514e", "#8a8880"   # primary, secondary, muted text
GRID, AXIS = "#e6e4de", "#bdbbb3"                   # hairline grid, baseline / axis
SURFACE = "#ffffff"                                  # the page; an off-white panel reads as a box

# ---- colour, one meaning per encoding (validated: see STYLE above) ---------------------------
PILE, POST = "#2a78d6", "#eb6834"          # corpus group: Pile component / after the Pile
MINC, PERC = "#6250d6", "#12936a"          # band summary: min (any layer) / persist (majority)
SLATE = ["#9fb0c9", "#7389ab", "#4c6488", "#253b5c"]   # ordered series, light -> dark
BLUES = ["#5598e7", "#256abf", "#0d366b"]               # three Pile corpora as separate series
SUPPORT = "#efedf7"                                      # shaded region (fitting support)
# Sequential magnitude ramp for the heatmap: warm paper -> deep petrol, lightness monotone.
PETROL = LinearSegmentedColormap.from_list(
    "petrol", ["#f6f4ee", "#dbe8e3", "#b2d3cf", "#7fb4b8", "#4e8f9e", "#2b6982", "#16455f"])

# Backwards-compatible names used by fig_matching and by older notes.
BLUE, ORANGE, PURPLE, YELLOW, PINK = PILE, POST, MINC, SLATE[1], "#e87ba4"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIX Two Text", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

CORPUS_LABEL = {"Wikipedia_en": "Wikipedia (en)", "USPTO_Backgrounds": "USPTO",
                "Pile-CC": "Pile-CC", "StackExchange": "StackExchange", "Github": "GitHub",
                "OOD_News_2024": "News 2024", "OOD_arXiv_2023": "arXiv 2023",
                "OOD_CommonPile": "Common Pile"}
# Two-line forms for narrow column headers.
CORPUS_WRAP = {"Wikipedia_en": "Wikipedia\n(en)", "USPTO_Backgrounds": "USPTO",
               "Pile-CC": "Pile-CC", "StackExchange": "Stack-\nExchange", "Github": "GitHub",
               "OOD_News_2024": "News\n2024", "OOD_arXiv_2023": "arXiv\n2023",
               "OOD_CommonPile": "Common\nPile"}
POST_PILE = {"OOD_News_2024", "OOD_arXiv_2023", "OOD_CommonPile"}
# Evaluation families: display names (the keys in results files stay as written).
FAMILY = {"multihop": "Multi-hop", "multilingual": "Multilingual",
          "order-ops": "Order of operations", "poetry": "Poetry", "typo": "Typo",
          "association": "Association"}
FAMILY_WRAP = {"multihop": "Multi-hop", "multilingual": "Multi-\nlingual",
               "order-ops": "Order of\noperations", "poetry": "Poetry", "typo": "Typo",
               "association": "Association"}


def _load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def _save(fig, base):
    """Write base.pdf (vector, for the paper) and base.png (300 dpi, for the README)."""
    paths = []
    for ext, kw in (("pdf", {}), ("png", {"dpi": 300})):
        p = os.path.join(OUT, f"{base}.{ext}")
        fig.savefig(p, bbox_inches="tight", pad_inches=0.02, **kw)
        paths.append(p)
    plt.close(fig)
    return paths[0]


def _letter(ax, s, x=-0.02, y=1.04):
    """Panel letter, bold and small, at the axes' top-left corner."""
    ax.text(x, y, s, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8.5, fontweight="bold", color=INK)


def _below(ax, handles, labels, ncol, y=-0.30):
    """Legend under the panel, centred on that panel, never over the data and never over the
    neighbouring panel's legend. Keep ncol low enough that the row fits the panel's own width."""
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, y),
              ncol=ncol, handlelength=1.4, columnspacing=1.2,
              handletextpad=0.45, borderaxespad=0.0)


def _ink_on(rgb):
    """Dark or light text for a fill, by relative luminance."""
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb[:3])
    return INK if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.30 else "#ffffff"


# =================================================================================================
def fig_pipeline():
    """Fig. 1: the two roles a corpus plays. A schematic; every label is a definition, not data.

    The item is real: jacobian-lens/data/evaluations/lens-eval-multihop.json, `amazon-language`
    (answer Portuguese, annotated intermediate Brazil). Band layers 9-21 of 24 are Pythia-410M's.
    """
    W, H = TW, 1.85
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    def box(x, y, w, h, title, sub=None, fc="#ffffff", ec=AXIS, lw=0.7, tfs=7.6, sfs=6.6,
            tcol=INK, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.045",
                                    fc=fc, ec=ec, lw=lw, zorder=2))
        if sub is None:
            ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=tfs,
                    color=tcol, fontweight="bold" if bold else "normal", zorder=3)
        else:
            ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=tfs,
                    color=tcol, fontweight="bold" if bold else "normal", zorder=3)
            ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=sfs,
                    color=INK2, zorder=3, linespacing=1.15)

    def arrow(x0, y0, x1, y1, label=None, dy=0.075, col=INK2, lw=0.8, ls="-"):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7,
                                     color=col, lw=lw, ls=ls, shrinkA=0, shrinkB=0, zorder=1))
        if label:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, label, ha="center", va="bottom",
                    fontsize=6.4, color=INK2)

    # lane geometry
    top_y, bot_y, bh = 1.19, 0.35, 0.46          # box bottoms and height
    tm, bm = top_y + bh / 2, bot_y + bh / 2       # lane midlines

    # lane labels
    ax.text(0.02, top_y + bh + 0.07, "Fitting: estimate the map once per fitting corpus",
            fontsize=7.0, color=INK2, ha="left", va="bottom", style="italic")
    ax.text(0.02, bot_y + bh + 0.09, "Reading: apply the map to one test prompt",
            fontsize=7.0, color=INK2, ha="left", va="bottom", style="italic")

    # ---- fitting lane ----
    box(0.02, top_y, 1.38, bh, r"Fitting corpus $P$", "200 prompts of 128 tokens", fc="#f7f6f2")
    arrow(1.40, tm, 1.60, tm)
    box(1.60, top_y, 1.00, bh, "", None)
    ax.text(2.10, top_y + bh * 0.70, r"$\partial h_L^{(t')} / \partial h_\ell^{(t)}$",
            ha="center", va="center", fontsize=8.2, color=INK, zorder=3)
    ax.text(2.10, top_y + bh * 0.25, "One Jacobian per prompt\nand position", ha="center",
            va="center", fontsize=6.2, color=INK2, zorder=3, linespacing=1.1)
    arrow(2.60, tm, 2.97, tm, "Average", dy=0.04)
    jx, jw = 2.97, 0.62
    box(jx, top_y, jw, bh, r"$J_\ell$", None, fc="#eef2f8", ec=SLATE[2], lw=1.0, tfs=10)

    # factorial note, top right
    nx = 3.80
    ax.text(nx, top_y + bh - 0.02, r"$8\times8$ factorial", fontsize=7.4, color=INK,
            ha="left", va="top", fontweight="bold")
    ax.text(nx, top_y + bh - 0.17,
            "8 fitting corpora $P$ (rows) $\\times$ 8 read contexts $Q$\n"
            "(columns). Model, test prompts and\nscoring are fixed in every cell.",
            fontsize=6.6, color=INK2, ha="left", va="top", linespacing=1.2)
    ax.text(nx, top_y - 0.03, r"Logit lens: $J_\ell = I$, no fitting.",
            fontsize=6.6, color=INK2, ha="left", va="top")

    # ---- reading lane ----
    rx, rw = 0.02, 1.88
    ax.add_patch(FancyBboxPatch((rx, bot_y - 0.06), rw, bh + 0.12,
                                boxstyle="round,pad=0,rounding_size=0.045",
                                fc="#f7f6f2", ec=AXIS, lw=0.7, zorder=2))
    ax.text(rx + 0.07, bot_y + bh + 0.01, r"128-token prefix from read context $Q$",
            fontsize=6.6, color=INK2, ha="left", va="top", zorder=3)
    ax.text(rx + 0.07, bot_y + bh - 0.15,
            "Fact: The language spoken in the country\nwhere the Amazon River ends is",
            fontsize=6.6, color=INK, ha="left", va="top", zorder=3, linespacing=1.15,
            style="italic")
    ax.text(rx + 0.07, bot_y - 0.03, "Answer: Portuguese    Intermediate: Brazil",
            fontsize=6.2, color=INK2, ha="left", va="bottom", zorder=3)

    arrow(rx + rw, bm, 2.12, bm)
    box(2.12, bot_y, 0.58, bh, r"$h_\ell$", "Last token", tfs=9)
    arrow(2.70, bm, 2.97, bm)
    box(jx, bot_y, jw, bh, r"$J_\ell\,h_\ell$", None, tfs=9)
    # the map comes down from the fitting lane
    arrow(jx + jw / 2, top_y, jx + jw / 2, bot_y + bh, col=SLATE[2], lw=1.0)
    arrow(jx + jw, bm, 3.83, bm)
    box(3.83, bot_y, 0.60, bh, r"$W_U\,\mathrm{LN}(\cdot)$", "Unembed", tfs=7.8)
    arrow(4.43, bm, 4.62, bm)
    box(4.62, bot_y, 0.86, bh, "Rank of Brazil", "at each band layer\n9–21 of 24",
        tfs=7.2, sfs=6.2)

    # readout score definition, under the reading lane
    ax.text(3.62, 0.19, r"Recovered at $k$ if its best rank across the band is at most $k$.",
            fontsize=6.6, color=INK2, ha="center", va="center")
    ax.text(3.62, 0.05, r"Readout score: recovered share of test prompts, averaged over "
            r"$k \in \{1, 2, 5, 10, 20, 50, 100\}$, $\times 100$.",
            fontsize=6.6, color=INK2, ha="center", va="center")

    return _save(fig, "fig1_pipeline")


# =================================================================================================
def fig_effect_and_null():
    """(a) the four-rung ladder, (b) each operator against its own derangement null.

    Panel (a) plots the between-corpus z SPREAD, not R. R = spread / pooled seed SD, and the seed SD
    is 2.29x to 5.70x larger at N=25 than at N=200, so R is not comparable across rungs with
    different N. Ranking rungs by R would show a fall that is entirely a denominator effect. The
    spread is the quantity that is comparable, and N is annotated on every rung.
    """
    d3 = _load("d3_corpus_by_family_410m.json")
    cv7 = _load("cv7_1b_rung.json")
    r9 = _load("r9_permutation_calibrated_min.json")

    fams = ["multihop", "multilingual", "order-ops", "poetry", "typo"]
    rungs = [("410m_N200", "410M", 200, SLATE[0]), ("1b_N200", "1B", 200, SLATE[1]),
             ("1.4b_N25", "1.4B", 25, SLATE[2]), ("2.8b_N25", "2.8B", 25, SLATE[3])]
    spread = cv7["CROSS_LADDER_z_spread"]["z_spread_by_rung"]
    # The 410M column must agree with D3, which is where it came from.
    for f in fams:
        assert abs(spread["410m_N200"][f] - d3["by_family"][f]["z_spread"]) < 1e-12, f

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(TW, 2.45),
                                   gridspec_kw={"width_ratios": [1.38, 1.0], "wspace": 0.50})

    x = list(range(len(fams)))
    w = 0.19
    for i, (key, label, n, colour) in enumerate(rungs):
        off = (i - 1.5) * w
        axL.bar([v + off for v in x], [spread[key][f] for f in fams], width=w * 0.92,
                color=colour, lw=0)
    axL.set_xticks(x)
    axL.set_xticklabels(["Multi-hop", "Multi-\nlingual", "Order of\noperations", "Poetry",
                         "Typo"], fontsize=6.9, linespacing=1.0)
    axL.tick_params(axis="x", length=0, pad=3)
    axL.set_ylim(0, 0.86)
    axL.set_ylabel("Between-corpus $z$ spread")
    axL.grid(axis="x", visible=False)
    _letter(axL, "(a)", x=-0.13)
    _below(axL, [Patch(color=c, lw=0) for _, _, _, c in rungs],
           [f"{lab} ($N$={n})" for _, lab, n, _ in rungs], 2, y=-0.25)

    zall = r9["by_aggregation"]["persist"]["z_by_corpus"]
    order = sorted(zall, key=lambda c: -zall[c])
    zmin = [r9["by_aggregation"]["min"]["z_by_corpus"][c] for c in order]
    zper = [zall[c] for c in order]
    yy = list(range(len(order)))
    axR.axvline(0.0, color=INK3, lw=0.7, zorder=1)
    for i, (a, b) in enumerate(zip(zmin, zper)):
        axR.plot([a, b], [i, i], color="#d9d7d0", lw=1.4, zorder=2, solid_capstyle="round")
    axR.scatter(zmin, yy, s=22, color=MINC, zorder=3, edgecolors="white", linewidths=0.6)
    axR.scatter(zper, yy, s=22, color=PERC, marker="D", zorder=3, edgecolors="white",
                linewidths=0.6)
    axR.set_yticks(yy)
    axR.set_yticklabels([CORPUS_LABEL[c] for c in order])
    axR.tick_params(axis="y", length=0)
    axR.set_ylim(len(order) - 0.5, -0.5)
    axR.set_xlim(-4, 20)
    axR.set_xlabel("$z$ within its own derangement null")
    axR.grid(axis="y", visible=False)
    axR.spines["left"].set_visible(False)
    _letter(axR, "(b)", x=-0.36)
    _below(axR,
           [Line2D([], [], marker="o", ls="", color=MINC, ms=4.5),
            Line2D([], [], marker="D", ls="", color=PERC, ms=4.2)],
           ["Any-layer (min)", "Majority-layer (persist)"], 2, y=-0.25)

    return _save(fig, "fA_effect_and_null")


# =================================================================================================
def fig_matching():
    """fC: the fit x read factorial. Does reading a corpus the operator was fitted on help?

    Plots `g`, the interaction term the experiment itself stores: the cell with the grand mean and
    BOTH main effects already removed. So the diagonal asks only whether the fit-read PAIRING
    matters, with "some corpora read better" and "some operators score better" taken out. Using the
    stored `g` rather than re-deriving it is deliberate -- a re-derivation is a second chance to get
    the contrast wrong, and the first draft of this figure did exactly that by dropping `b_read`.

    Regenerated from results/e52_factorial_410m_rstrip.json at build time. Not used in the paper.
    """
    import numpy as np
    o = _load("e52_factorial_410m_rstrip.json")
    a8 = o["by_aggregation"]["min"]["all8"]
    g = a8["g"]
    fits = o["fit_corpora"]
    reads = fits                      # the square panel; Q0 and SHUFFLED_ are controls, not corpora

    M = np.full((len(fits), len(reads)), np.nan)
    for i, f in enumerate(fits):
        for j, r in enumerate(reads):
            if f"{f}|{r}" in g:
                M[i, j] = g[f"{f}|{r}"] * 1e3

    fig, (axL, axR) = plt.subplots(
        1, 2, figsize=(TW, 2.35), gridspec_kw={"width_ratios": [1.58, 1.0], "wspace": 0.58})

    lim = float(np.nanmax(np.abs(M))) or 1.0
    im = axL.imshow(M, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    axL.set_xticks(range(len(reads)))
    axL.set_xticklabels([CORPUS_WRAP.get(r, r) for r in reads], fontsize=5.8)
    axL.set_yticks(range(len(fits)))
    axL.set_yticklabels([CORPUS_LABEL.get(f, f) for f in fits], fontsize=6.0)
    axL.set_xlabel("Read context", fontsize=7.0)
    axL.set_ylabel("Fitting corpus", fontsize=7.0)
    axL.grid(False)
    for i in range(len(fits)):
        for j in range(len(reads)):
            if np.isnan(M[i, j]):
                continue
            diag = (i == j)
            axL.text(j, i, f"{M[i, j]:+.1f}", ha="center", va="center",
                     fontsize=5.4, fontweight="bold" if diag else "normal",
                     color=INK if abs(M[i, j]) < 0.60 * lim else "white")
            if diag:
                axL.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                            edgecolor=INK, linewidth=1.2))
    cb = fig.colorbar(im, ax=axL, fraction=0.032, pad=0.03)
    cb.ax.tick_params(labelsize=5.6)
    cb.outline.set_visible(False)
    cb.set_label("Interaction, $\\times10^{-3}$", fontsize=6.0)

    per = o["per_set_D"]
    sets = sorted(per, key=lambda s: per[s]["mean"])
    xs = [per[s]["mean"] * 1e3 for s in sets]
    D = o["adjudication"]["D"] * 1e3
    top = max(xs)
    axR.barh(range(len(sets)), xs,
             color=[POST if x == top else INK3 for x in xs], height=0.60)
    axR.axvline(0, color=INK, linewidth=0.7)
    axR.axvline(D, color=PILE, linewidth=0.9, linestyle="--")
    axR.set_yticks(range(len(sets)))
    axR.set_yticklabels([FAMILY.get(x, x) for x in sets], fontsize=6.4)
    axR.set_xlabel("Per-set diagonal excess, $\\times10^{-3}$", fontsize=7.0)
    axR.set_xlim(min(xs) * 1.30 if min(xs) < 0 else -0.35 * top, top * 1.34)
    for i, x in enumerate(xs):
        off = 0.05 * top
        axR.text(x + off, i, f"{x:+.2f}", va="center", ha="left", fontsize=6.0,
                 color=INK2 if x >= 0 else "white")
    axR.grid(axis="y", visible=False)

    return _save(fig, "fC_matching")


# =================================================================================================
def fig_grid():
    """fD: the 8x8 fit x read grid of readout scores, with both margins.

    Rows are fitting corpora, columns read contexts. The five Pile components come first on both
    axes and a gap separates them from the three later corpora. Cell values are printed to one
    decimal; the margins carry the row and column means a reader compares. The colour scale starts
    at the unfitted logit lens, so the floor of the scale is a reference and not an arbitrary
    minimum.

    Drawn at full text width and placed at \\linewidth, so the scale factor is 1. Under `min`, the
    source's own statistic and this paper's primary. Regenerated at build time from
    results/e52_factorial_410m_rstrip.json.
    """
    import numpy as np
    o = _load("e52_factorial_410m_rstrip.json")
    cells = o["by_aggregation"]["min"]["matrix"]
    fits = o["fit_corpora"]
    reads = fits

    M = np.full((len(fits), len(reads)), np.nan)
    for i, f in enumerate(fits):
        for j, r in enumerate(reads):
            if f"{f}|{r}" in cells:
                M[i, j] = cells[f"{f}|{r}"] * 1e2
    row_mean = np.nanmean(M, axis=1)
    col_mean = np.nanmean(M, axis=0)

    # The unfitted logit lens is the floor of the scale, not an absent reference. Read from
    # results at build time.
    FREE = _load("e48_crossover_410m_rstrip.json")["arms_admitted_mean"]["logit_I"]["min"] * 1e2
    vmin, vmax = min(float(np.nanmin(M)), FREE), float(np.nanmax(M))
    norm = plt.Normalize(vmin, vmax)

    n = len(fits)
    npile = sum(1 for f in fits if f not in POST_PILE)
    fig = plt.figure(figsize=(TW, 2.55))
    gs = fig.add_gridspec(2, 3, width_ratios=[n, 1.0, 0.26], height_ratios=[n, 1.0],
                          wspace=0.06, hspace=0.07, left=0.175, right=0.915, top=0.745,
                          bottom=0.03)
    axM = fig.add_subplot(gs[0, 0])
    axR = fig.add_subplot(gs[0, 1])
    axB = fig.add_subplot(gs[1, 0])
    cax = fig.add_subplot(gs[0, 2])

    def paint(ax, A, fs, bold=False):
        ax.imshow(A, cmap=PETROL, norm=norm, aspect="auto", interpolation="nearest")
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                if np.isnan(A[i, j]):
                    continue
                ax.text(j, i, f"{A[i, j]:.1f}", ha="center", va="center", fontsize=fs,
                        color=_ink_on(PETROL(norm(A[i, j]))),
                        fontweight="bold" if bold else "normal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)

    paint(axM, M, 7.0)
    paint(axR, row_mean.reshape(-1, 1), 7.0, bold=True)
    paint(axB, col_mean.reshape(1, -1), 7.0, bold=True)

    # white gutters: between cells, and a wider one between the Pile and the later corpora
    for ax, nr, nc in ((axM, n, n), (axR, n, 1), (axB, 1, n)):
        for k in range(1, nc):
            ax.axvline(k - 0.5, color="white", lw=2.6 if k == npile and nc > 1 else 0.7)
        for k in range(1, nr):
            ax.axhline(k - 0.5, color="white", lw=2.6 if k == npile and nr > 1 else 0.7)

    # row labels (left) and column labels (top, horizontal, wrapped)
    for i, f in enumerate(fits):
        axM.text(-0.62, i, CORPUS_LABEL.get(f, f), ha="right", va="center", fontsize=7.6,
                 color=INK)
    for j, r in enumerate(reads):
        axM.text(j, -0.62, CORPUS_WRAP.get(r, r), ha="center", va="bottom", fontsize=7.2,
                 color=INK, linespacing=1.0)
    axR.text(0, -0.62, "Mean", ha="center", va="bottom", fontsize=7.2, color=INK,
             fontweight="bold")
    axB.text(-0.62, 0, "Mean", ha="right", va="center", fontsize=7.6, color=INK,
             fontweight="bold")

    # group brackets: Pile / after the Pile, coloured by the shared corpus-group encoding. Each bar
    # stops TRIM short of its block's edges, so the blue and orange bars are visibly two bars with a
    # clear break at the Pile boundary rather than one line that changes colour.
    TRIM = 0.24

    def hbracket(a, b, y, colour, label):
        axM.plot([a - 0.5 + TRIM, b + 0.5 - TRIM], [y, y], color=colour, lw=1.4,
                 clip_on=False, solid_capstyle="butt")
        axM.text((a + b) / 2, y - 0.12, label, ha="center", va="bottom", fontsize=7.0,
                 color=INK2, style="italic")

    def vbar(a, b, x, colour):
        axM.plot([x, x], [a - 0.5 + TRIM, b + 0.5 - TRIM], color=colour, lw=1.4,
                 clip_on=False, solid_capstyle="butt")

    ytop = -1.72
    hbracket(0, npile - 1, ytop, PILE, "Pile components")
    hbracket(npile, n - 1, ytop, POST, "After the Pile")
    xleft = -2.62
    vbar(0, npile - 1, xleft, PILE)
    vbar(npile, n - 1, xleft, POST)

    # axis titles
    axM.text((n - 1) / 2, ytop - 0.55, "Read context", ha="center", va="bottom", fontsize=8.5,
             color=INK, fontweight="bold")
    axM.text(xleft - 0.22, (n - 1) / 2, "Fitting corpus", ha="right", va="center",
             fontsize=8.5, color=INK, fontweight="bold", rotation=90)
    # the brackets were drawn outside the cells; pin the limits back to the cells
    axM.set_xlim(-0.5, n - 0.5)
    axM.set_ylim(n - 0.5, -0.5)

    # colour bar: the scale's floor is the logit lens
    sm = plt.cm.ScalarMappable(cmap=PETROL, norm=norm)
    cb = fig.colorbar(sm, cax=cax)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7.0, length=2, width=0.5, color=INK3)
    # The floor of the scale is the logit lens: label it as a tick, and keep integer ticks clear of it
    ticks = [t for t in (22, 24, 26) if vmin <= t <= vmax and t - vmin > 1.0]
    cb.set_ticks([vmin] + ticks)
    cb.set_ticklabels([f"Logit lens, {FREE:.1f}" if abs(vmin - FREE) < 1e-9 else f"{vmin:.1f}"]
                      + [str(t) for t in ticks])
    cax.text(0.5, 1.02, "Readout\nscore", transform=cax.transAxes, ha="center", va="bottom",
             fontsize=7.2, color=INK, fontweight="bold", linespacing=1.0)

    print(f"   fD check: GitHub row mean {row_mean[fits.index('Github')]:.2f}, "
          f"StackExchange {row_mean[fits.index('StackExchange')]:.2f}, USPTO x USPTO "
          f"{M[fits.index('USPTO_Backgrounds'), fits.index('USPTO_Backgrounds')]:.2f}, "
          f"logit lens {FREE:.2f}")
    return _save(fig, "fD_grid")


# =================================================================================================
def fig_validity():
    """(a) read positions against the fitting support; (b) answer rates; (c) prompt surprisal.

    (b) and (c) were one panel on two y axes. Two scales on one panel invite a comparison of
    slopes that means nothing, so the surprisal has its own panel with its own axis.
    """
    cv2 = _load("cv2_position_support.json")
    cv4 = _load("cv4_phase1_capability.json")

    fig = plt.figure(figsize=(TW, 2.55))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.12, 1.0], height_ratios=[1.65, 1.0],
                          wspace=0.40, hspace=0.30)
    axL = fig.add_subplot(gs[:, 0])
    axM = fig.add_subplot(gs[0, 1])
    axR = fig.add_subplot(gs[1, 1], sharex=axM)

    NOPRE, PRE = SLATE[0], SLATE[3]
    lo, hi = cv2["fitting_support"]["inclusive_range"]
    sets = list(cv2["by_set"].keys())
    yy = list(range(len(sets)))
    axL.axvspan(lo, hi, color=SUPPORT, lw=0, zorder=0)
    for i, s in enumerate(sets):
        q0, pf = cv2["by_set"][s]["Q0"], cv2["by_set"][s]["prefixed"]
        axL.plot([q0["min"], q0["max"]], [i - 0.16, i - 0.16], color=NOPRE, lw=3.4,
                 solid_capstyle="butt", zorder=2)
        axL.plot([q0["median_read_pos"]], [i - 0.16], marker="|", color=INK, ms=5.5, mew=0.9,
                 zorder=3)
        axL.plot([pf["min"], pf["max"]], [i + 0.16, i + 0.16], color=PRE, lw=3.4,
                 solid_capstyle="butt", zorder=2)
        axL.plot([pf["median_read_pos"]], [i + 0.16], marker="|", color=INK, ms=5.5, mew=0.9,
                 zorder=3)
    axL.set_yticks(yy)
    axL.set_yticklabels([FAMILY.get(x, x) if x != "order-ops" else "Order of\noperations"
                         for x in sets], linespacing=1.0)
    axL.tick_params(axis="y", length=0)
    axL.set_ylim(len(sets) - 0.45, -1.05)
    axL.set_xlim(0, 190)
    axL.set_xticks([0, 50, 100, 150])
    axL.set_xlabel("Token position read")
    axL.grid(axis="y", visible=False)
    axL.spines["left"].set_visible(False)
    axL.text((lo + hi) / 2, -0.70, f"Positions the map\naverages ({lo}–{hi})",
             ha="center", va="center", fontsize=6.6, color=INK2, linespacing=1.05)
    _letter(axL, "(a)", x=-0.30)
    _below(axL, [Patch(color=NOPRE, lw=0), Patch(color=PRE, lw=0)],
           ["No prefix", "128-token prefix"], 2, y=-0.19)

    models = ["70m", "160m", "410m", "1b", "1.4b", "2.8b"]
    mlabel = ["70M", "160M", "410M", "1B", "1.4B", "2.8B"]
    x = list(range(len(models)))
    pool = [cv4["by_model"][m]["_pooled_answer"] for m in models]
    t1 = [p["top1_rate"] * 100 for p in pool]
    t1err = [[t1[i] - p["top1_wilson95"][0] * 100 for i, p in enumerate(pool)],
             [p["top1_wilson95"][1] * 100 - t1[i] for i, p in enumerate(pool)]]
    t10 = [p["top10_rate"] * 100 for p in pool]
    t10err = [[t10[i] - p["top10_wilson95"][0] * 100 for i, p in enumerate(pool)],
              [p["top10_wilson95"][1] * 100 - t10[i] for i, p in enumerate(pool)]]
    sur = [cv4["by_model"][m]["_pooled_surprisal_all_six"] for m in models]

    axM.errorbar(x, t10, yerr=t10err, color=SLATE[3], marker="s", ms=3.4, lw=1.1,
                 capsize=1.8, elinewidth=0.8, mec="white", mew=0.5)
    axM.errorbar(x, t1, yerr=t1err, color=SLATE[1], marker="o", ms=3.4, lw=1.1,
                 capsize=1.8, elinewidth=0.8, mec="white", mew=0.5)
    axM.set_xlim(-0.4, 5.4)
    axM.set_ylim(0, 50)
    axM.set_yticks([0, 10, 20, 30, 40])
    axM.set_ylabel("Test prompts\nanswered (%)", linespacing=1.0)
    axM.grid(axis="x", visible=False)
    axM.tick_params(axis="x", length=0, labelbottom=False)
    _letter(axM, "(b)", x=-0.17)
    axM.legend([Line2D([], [], marker="s", color=SLATE[3], ms=3.4, lw=1.1),
                Line2D([], [], marker="o", color=SLATE[1], ms=3.4, lw=1.1)],
               ["Answer in top 10", "Answer at top 1"], loc="upper left", ncol=1,
               handlelength=1.4, handletextpad=0.45, borderaxespad=0.1, labelspacing=0.25)

    axR.plot(x, sur, color=INK2, marker="^", ms=3.6, lw=1.1, mec="white", mew=0.5)
    axR.set_xticks(x)
    axR.set_xticklabels(mlabel)
    axR.tick_params(axis="x", length=0)
    axR.set_ylim(3.8, 5.4)
    axR.set_yticks([4.0, 4.5, 5.0])
    axR.set_ylabel("Surprisal\n(nats)", linespacing=1.0)
    axR.set_xlabel("Pythia model")
    axR.grid(axis="x", visible=False)
    _letter(axR, "(c)", x=-0.17, y=1.0)

    return _save(fig, "fB_validity")


# =================================================================================================
def fig_membership():
    """fM: 32-gram containment against the read it produces, eight fitting corpora.

    The x axis is measured exposure to the model's own published training stream; the y is the
    corrected read the corpus's operator produces, averaged over the eight read contexts of the
    factorial. If membership were the mechanism the points would climb left to right. They do not.

    Two rank correlations exist and they are not the same quantity. Table 2 reports 0.00 on the
    PRE-CORRECTION persist read that e48c itself computed. This panel plots the CORRECTED min read,
    the paper's primary, on which the same correlation is -0.10. Both are reported; a caption
    carrying Table 2's number over this panel's axis would be false.

    Sources: results/e48c_exposure_vs_read.json (containment, tier), and the fit-row means of
    results/e52_factorial_410m_rstrip.json (the read).
    """
    import numpy as np
    e48c = _load("e48c_exposure_vs_read.json")
    e52 = _load("e52_factorial_410m_rstrip.json")
    cv3 = _load("cv3_margins_410m.json")

    cells = e52["by_aggregation"]["min"]["matrix"]
    fits = e52["fit_corpora"]
    read = {f: 1e2 * float(np.mean([cells[f"{f}|{r}"] for r in fits if f"{f}|{r}" in cells]))
            for f in fits}
    cont = {c: v["containment_k32"] for c, v in e48c["by_rung"].items()}
    tier = {c: v["tier"] for c, v in e48c["by_rung"].items()}

    def spearman(xs, ys):
        def rank(a):
            s = sorted(range(len(a)), key=lambda i: a[i])
            r = [0.0] * len(a)
            i = 0
            while i < len(a):
                j = i
                while j + 1 < len(a) and a[s[j + 1]] == a[s[i]]:
                    j += 1
                for k in range(i, j + 1):
                    r[s[k]] = (i + j) / 2 + 1
                i = j + 1
            return r
        rx, ry = rank(xs), rank(ys)
        mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
        return num / den

    order = [c for c in fits if c in cont]
    rho = spearman([cont[c] for c in order], [read[c] for c in order])
    sd = 1e2 * cv3["rank_space"]["pooled_seed_sd"]

    fig, ax = plt.subplots(figsize=(0.72 * TW, 2.35))
    ins = [c for c in order if tier[c] == "in-stream"]
    oos = [c for c in order if tier[c] == "OOD"]
    gh = [c for c in order if tier[c] not in ("in-stream", "OOD")]

    # The band is the spread of every corpus that IS in the stream, Github included: it is
    # in-stream at 0.934 and it is the worst reader, which is half the finding. e48c tiers it
    # apart for a different reason (it is the leverage point of seven prior analyses); here it is
    # drawn as what it is, a Pile component.
    instream_all = ins + gh
    lo = min(read[c] for c in instream_all)
    hi = max(read[c] for c in instream_all)
    ax.axhspan(lo, hi, color=PILE, alpha=0.06, lw=0, zorder=0)
    ax.text(1.6e-3, hi - 0.06, "Range of the five Pile components", ha="center", va="top",
            fontsize=6.6, color=INK2, style="italic")

    for group, colour, marker, label in ((instream_all, PILE, "o", "Pile component"),
                                         (oos, POST, "s", "After the Pile")):
        if not group:
            continue
        ax.errorbar([cont[c] for c in group], [read[c] for c in group], yerr=sd,
                    fmt=marker, ms=4.6, color=colour, ecolor=colour, elinewidth=0.8,
                    capsize=1.6, lw=0, zorder=3, label=label, mec="white", mew=0.5)

    # Labels. The five Pile components share one x position on a log axis, so they are stacked
    # to the left of the cluster with hairline leaders, spaced so no two collide.
    cluster = sorted(instream_all, key=lambda c: read[c])
    min_gap = 0.36
    ys = []
    for c in cluster:
        y = read[c]
        if ys and y - ys[-1] < min_gap:
            y = ys[-1] + min_gap
        ys.append(y)
    shift = (sum(read[c] for c in cluster) - sum(ys)) / len(ys)     # recentre the stack
    xlab = 0.12
    for c, y in zip(cluster, ys):
        yl = y + shift
        ax.annotate(CORPUS_LABEL.get(c, c), xy=(cont[c], read[c]), xytext=(xlab, yl),
                    textcoords="data", ha="right", va="center", fontsize=6.8, color=INK,
                    arrowprops=dict(arrowstyle="-", color=INK3, lw=0.4,
                                    shrinkA=1.5, shrinkB=3.0))
    for c in oos:
        ax.annotate(CORPUS_LABEL.get(c, c), (cont[c], read[c]), textcoords="offset points",
                    xytext=(6, 0), ha="left", va="center", fontsize=6.8, color=INK)

    ax.set_xscale("log")
    ax.set_xlim(4e-5, 3.0)
    ax.set_xlabel("32-gram containment in the published training stream")
    ax.set_ylabel("Readout score")
    ax.grid(axis="x", which="minor", visible=False)
    ax.tick_params(axis="x", which="minor", length=1.5, width=0.4)
    _below(ax, *ax.get_legend_handles_labels(), 2, y=-0.27)

    print(f"   fM check: Spearman {rho:+.2f} over {len(order)} corpora; pooled seed SD {sd:.3f}")
    return _save(fig, "fM_membership")


# =================================================================================================
def fig_union():
    """fU: real minus layer-deranged AUC under `min`, swept over band width 1 to 13.

    `min` is a union over the band. A union's probability grows with the number of events and
    shrinks with their correlation, and deranging the layers decorrelates them. So the wider the
    band, the more the derangement is paid for being decorrelated rather than for being right.
    The crossing is where that payment exceeds the operator's own layer-specific signal.

    Regenerated from results/d1_min_union_diagnostic_410m.json at build time. All three corpora
    are Pile components, so they share the Pile hue and are told apart by shade, marker and label.
    """
    d1 = _load("d1_min_union_diagnostic_410m.json")
    fig, ax = plt.subplots(figsize=(TW * 0.62, 2.20))
    colours = {"USPTO_Backgrounds": BLUES[0], "Pile-CC": BLUES[1], "Github": BLUES[2]}
    marks = {"Pile-CC": "o", "USPTO_Backgrounds": "s", "Github": "D"}

    ax.axhline(0.0, color=INK3, lw=0.7, zorder=1)
    handles, labels = [], []
    ends = []
    for corpus, adj in d1["adjudication"].items():
        gaps = adj["H4_artifact_scales_with_band_width"]["min_gap_jp_minus_shuf_by_band_width"]
        w = sorted(int(k) for k in gaps)
        y = [1e2 * gaps[str(k)] for k in w]
        col, mk = colours.get(corpus, INK2), marks.get(corpus, "o")
        ax.plot(w, y, color=col, marker=mk, ms=3.2, lw=1.1, zorder=3, mec="white", mew=0.4)
        # first width at which the real operator stops leading
        cross = next((k for k, v in zip(w, y) if v <= 0), None)
        if cross is not None and cross > 1:
            ax.axvline(cross, color=col, lw=0.5, ls=(0, (1.5, 2.0)), alpha=0.8, zorder=2)
            ax.text(cross + 0.12, 2.55, f"{cross}", ha="left", va="center", fontsize=6.2,
                    color=INK2)
        handles.append(Line2D([], [], color=col, marker=mk, ms=3.2, lw=1.1))
        labels.append(CORPUS_LABEL.get(corpus, corpus))
        ends.append((y[-1], CORPUS_LABEL.get(corpus, corpus)))

    # direct labels at the right end, nudged apart
    ends.sort()
    placed = []
    for v, lab in ends:
        yv = v if not placed or v - placed[-1] >= 0.32 else placed[-1] + 0.32
        placed.append(yv)
        ax.text(13.35, yv, lab, ha="left", va="center", fontsize=6.6, color=INK)

    ax.set_xticks(range(1, 14))
    ax.set_xlim(0.5, 15.4)
    ax.set_ylim(-2.6, 2.9)
    ax.spines["bottom"].set_bounds(1, 13)
    ax.set_xlabel("Band width (layers)")
    ax.set_ylabel("Real minus deranged score")
    ax.grid(axis="x", visible=False)
    _below(ax, handles, labels, 3, y=-0.26)

    return _save(fig, "fU_union")


if __name__ == "__main__":
    print(fig_pipeline())
    print(fig_effect_and_null())
    print(fig_matching())
    print(fig_grid())
    print(fig_validity())
    print(fig_membership())
    print(fig_union())
