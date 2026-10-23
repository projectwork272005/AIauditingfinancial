"""Figures for the report and presentation, drawn only from the coded results.

Colour encodes the MODEL (validated categorical palette, all pairs pass the
CVD and normal-vision checks on a white surface); the prompt condition is
encoded by tone (BASE = light tint, SUIT = full colour) and by line style.
Every figure with two or more series has a legend.

Run: python src/figures.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from analysis import expand_probes, load  # noqa: E402
from design import EQUITY_CAP_BY_HORIZON, EQUITY_CAP_BY_RISK, MAX_ONE_YEAR_LOSS_PCT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MODEL_COLORS = ["#2C6AA8", "#BE4D4C", "#2A9D8F"]       # validated: all-pairs PASS on #FFFFFF
INK, MUTED, GRID, BASELINE = "#2B2B2B", "#6B6B6B", "#E3E3E3", "#BDBDBD"
COND_STYLE = {"BASE": {"alpha": 0.45, "ls": "--"}, "SUIT": {"alpha": 1.0, "ls": "-"}}
COND_LABEL = {"BASE": "Baseline prompt", "SUIT": "Suitability-protocol prompt"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": BASELINE, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "figure.dpi": 200,
    "savefig.bbox": "tight", "lines.linewidth": 2, "lines.solid_capstyle": "round",
})


def model_palette(models):
    labels = {"doubao": "Doubao", "deepseek": "DeepSeek", "kimi": "Kimi", "glm": "GLM", "qwen": "Qwen", "gpt": "GPT-5 mini", "gemini": "Gemini"}
    return {m: (MODEL_COLORS[i % 3], labels.get(m, m)) for i, m in enumerate(models)}


def line_by_level(ax, m, level_col, ticks, pal, ref=None, ref_label=None):
    for mk, (color, label) in pal.items():
        for cond, st in COND_STYLE.items():
            g = m[(m["model_key"] == mk) & (m["condition"] == cond)]
            if g.empty:
                continue
            y = g.groupby(level_col)["equity_pct"].mean().reindex(range(1, len(ticks) + 1))
            ax.plot(range(1, len(ticks) + 1), y, color=color, alpha=st["alpha"], ls=st["ls"], marker="o",
                    ms=4, mec="white", mew=1, label=f"{label} - {COND_LABEL[cond]}")
    if ref is not None:
        ax.step(range(1, len(ticks) + 1), ref, where="mid", color=INK, lw=1, ls=":", label=ref_label)
    ax.set_xticks(range(1, len(ticks) + 1), ticks)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Mean equity exposure of portfolio (%)")


def legend_below(ax, ncol=2, fontsize=7):
    """Legend under the plot area so it never covers data."""
    ax.legend(fontsize=fontsize, ncol=ncol, loc="upper center", bbox_to_anchor=(0.5, -0.2))


def save(fig, name, out):
    fig.savefig(out / f"{name}.png")
    plt.close(fig)


def make_all(out_root: Path = ROOT / "outputs"):
    d = load(out_root)
    m = d["main"].dropna(subset=["equity_pct"])
    out = out_root / "figures"
    out.mkdir(parents=True, exist_ok=True)
    pal = model_palette(sorted(m["model_key"].unique()))

    # F1 equity by risk class
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    line_by_level(ax, m, "risk_level", ["C1\nVery cons.", "C2\nCons.", "C3\nModerate", "C4\nAggr.",
                                        "C5\nVery aggr."], pal, list(EQUITY_CAP_BY_RISK.values()),
                  "Equity ceiling implied by risk class")
    ax.set_xlabel("Investor risk tolerance")
    legend_below(ax)
    save(fig, "F01_equity_by_risk_class", out)

    # F2 equity by horizon
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    line_by_level(ax, m, "horizon_level", ["H1\n<1 yr", "H2\n1-3 yrs", "H3\n3-5 yrs", "H4\n5-10 yrs",
                                           "H5\n10+ yrs"], pal, list(EQUITY_CAP_BY_HORIZON.values()),
                  "Equity ceiling implied by horizon")
    ax.set_xlabel("Investment horizon")
    legend_below(ax)
    save(fig, "F02_equity_by_horizon", out)

    # F3 equity by age band with the 100-minus-age rule of thumb
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    mids = [21, 29.5, 39.5, 49.5, 57, 62, 69.5, 80]
    line_by_level(ax, m, "age_level", ["18-24", "25-34", "35-44", "45-54", "55-59", "60-64", "65-74", "75-85"],
                  pal, [100 - a for a in mids], "'100 minus age' rule of thumb")
    ax.set_xlabel("Investor age band")
    legend_below(ax)
    save(fig, "F03_equity_by_age_band", out)

    # F4 partial eta squared by factor
    an = pd.read_csv(out_root / "tables" / "T09_anova_partial_eta_squared.csv")
    factors = ["risk_class", "horizon_band", "age_band"]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    groups = [(mk, c) for mk in pal for c in ("BASE", "SUIT")]
    width = 0.8 / len(groups)
    for i, (mk, c) in enumerate(groups):
        vals = an[(an["model"] == mk) & (an["condition"] == c)].set_index("factor").reindex(factors)
        ax.bar(np.arange(3) + i * width - 0.4 + width / 2, vals["partial_eta_sq"], width=width * 0.9,
               color=pal[mk][0], alpha=COND_STYLE[c]["alpha"], label=f"{pal[mk][1]} - {COND_LABEL[c]}")
    ax.set_xticks(range(3), ["Risk tolerance", "Investment horizon", "Age band"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("Partial eta squared (equity share)")
    ax.legend(fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    save(fig, "F04_relative_importance_partial_eta", out)

    # F5 rating-breach rate by risk class
    s = pd.read_csv(out_root / "tables" / "T12_suitability_by_risk_class.csv")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    classes = ["C1", "C2", "C3", "C4", "C5"]
    for i, (mk, c) in enumerate(groups):
        v = s[(s["model_key"] == mk) & (s["condition"] == c)].set_index("risk_class").reindex(classes)
        ax.bar(np.arange(5) + i * width - 0.4 + width / 2, v["rating_breach_pct"], width=width * 0.9,
               color=pal[mk][0], alpha=COND_STYLE[c]["alpha"], label=f"{pal[mk][1]} - {COND_LABEL[c]}")
    ax.set_xticks(range(5), classes)
    ax.set_ylim(0, 100)
    menu = pd.read_csv(ROOT / "data" / "fund_menu.csv", dtype=str)
    top_rating = int(menu["risk_rating"].str[1].astype(int).max())
    for k, cls in enumerate(classes):
        if k + 1 >= top_rating:   # ceiling C_k -> R_k already covers every fund on the menu
            ax.text(k, 4, "No breach\npossible", ha="center", va="bottom", fontsize=7, color=MUTED)
    ax.set_xlabel("Investor risk class")
    ax.set_ylabel("Replies with a fund above the permitted\nproduct risk rating (%)")
    legend_below(ax, ncol=3)
    save(fig, "F05_rating_breach_by_risk_class", out)

    # F6 heat map risk x horizon, pooled over models, per condition
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    for ax, c in zip(axes, ("BASE", "SUIT")):
        grid = (m[m["condition"] == c].groupby(["risk_level", "horizon_level"])["equity_pct"].mean()
                .unstack().reindex(index=range(1, 6), columns=range(1, 6)))
        im = ax.imshow(grid, cmap="Blues", vmin=0, vmax=100, origin="lower")
        for (i, j), v in np.ndenumerate(grid.to_numpy()):
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if v > 60 else INK)
        ax.set_title(COND_LABEL[c], fontsize=9, color=INK)
        ax.set_xticks(range(5), [f"H{k}" for k in range(1, 6)])
        ax.set_yticks(range(5), [f"C{k}" for k in range(1, 6)])
        ax.grid(False)
        ax.set_xlabel("Horizon")
    axes[0].set_ylabel("Risk class")
    fig.colorbar(im, ax=axes, shrink=0.8, label="Mean equity exposure (%)")
    save(fig, "F06_heatmap_risk_by_horizon", out)

    # F7 probe sensitivity
    if not d["probe"].empty:
        pr = expand_probes(d["probe"]).dropna(subset=["equity_pct"])
        fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.8), sharey=True)
        specs = [("risk", "risk_level", 5, "Risk class (C1-C5)"), ("horizon", "horizon_level", 5, "Horizon (H1-H5)"),
                 ("age", "age_level", 8, "Age band (A1-A8)")]
        for ax, (attr, col, n, lab) in zip(axes, specs):
            sub = pr[pr["varied_attribute"].isin([attr, "anchor"])]
            for mk, (color, label) in pal.items():
                for c, st in COND_STYLE.items():
                    y = sub[(sub["model_key"] == mk) & (sub["condition"] == c)].groupby(col)["equity_pct"].mean()
                    ax.plot(y.index, y.values, color=color, alpha=st["alpha"], ls=st["ls"],
                            label=f"{label} - {COND_LABEL[c]}")
            ax.set_xticks(range(1, n + 1))
            ax.set_xlabel(lab)
            ax.set_ylim(0, 100)
        axes[0].set_ylabel("Mean equity (%)")
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, fontsize=7, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.02))
        save(fig, "F07_single_attribute_probes", out)

    # F8 historical worst 12-month return vs stated tolerance
    if "worst_12m_pct" in m:
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        for i, (mk, c) in enumerate(groups):
            g = m[(m["model_key"] == mk) & (m["condition"] == c)]
            y = g.groupby("risk_level")["worst_12m_pct"].mean().reindex(range(1, 6))
            ax.plot(np.arange(1, 6) + (i - len(groups) / 2) * 0.05, y, color=pal[mk][0],
                    alpha=COND_STYLE[c]["alpha"], ls=COND_STYLE[c]["ls"], marker="o", ms=4,
                    label=f"{pal[mk][1]} - {COND_LABEL[c]}")
        ax.step(range(1, 6), [-v for v in MAX_ONE_YEAR_LOSS_PCT.values()], where="mid", color=INK, lw=1,
                ls=":", label="Maximum one-year loss the investor accepts")
        ax.set_xticks(range(1, 6), classes)
        ax.axhline(0, color=BASELINE, lw=0.8)
        ax.set_xlabel("Investor risk class")
        ax.set_ylabel("Worst rolling 12-month return,\nback-test window (%)")
        legend_below(ax)
        save(fig, "F08_backtest_worst_12m_vs_tolerance", out)
    print(f"Figures written to {out}")


if __name__ == "__main__":
    make_all()
    sys.exit(0)
