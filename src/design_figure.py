"""Figure 1: schematic of the experimental pipeline (describes the procedure,
contains no results). Run: python src/design_figure.py"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED = "#2B2B2B", "#6B6B6B"
FILL = {"input": "#E8EFF7", "treat": "#F6E6E6", "run": "#F2F2F2", "eval": "#E3F2EF"}


def box(ax, x, y, w, h, title, lines, kind):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
                                fc=FILL[kind], ec="#BDBDBD", lw=0.8))
    ax.text(x + 0.03, y + h - 0.06, title, fontsize=8.5, fontweight="bold", color=INK, va="top")
    ax.text(x + 0.03, y + h - 0.2, "\n".join(lines), fontsize=7.2, color=INK, va="top", linespacing=1.35)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9, color=MUTED, lw=1))


def main():
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    ax.set_xlim(0, 4.3)
    ax.set_ylim(0, 2.45)
    ax.axis("off")
    c1, c2, c3, c4, w = 0.02, 1.12, 2.22, 3.3, 0.97
    box(ax, c1, 1.35, w, 1.05, "1  Synthetic investors",
        ["200 profiles, full factorial", "5 horizons x 5 risk classes", "x 8 age bands (1 per cell)",
         "+ 160 one-attribute probes"], "input")
    box(ax, c1, 0.05, w, 1.15, "2  Verified fund menu",
        ["23 real Chinese public funds", "14 managers; R1-R5 ratings", "cash, bond, hybrid, index,",
         "QDII, gold, pension FOF", "sources + retrieval dates"], "input")
    box(ax, c2, 1.35, w, 1.05, "3  Prompt condition",
        ["BASE: adviser role + menu", "+ JSON format", "SUIT: BASE + suitability", "protocol (C1-C5 -> R cap)"],
        "treat")
    box(ax, c2, 0.05, w, 1.15, "4  Three LLMs",
        ["Doubao, DeepSeek, Kimi", "via OpenRouter (pinned)", "same settings, JSON mode", "random call order",
         "2,508 planned calls"], "treat")
    box(ax, c3, 0.55, w, 1.35, "5  Log and code",
        ["append-only raw log", "prompt hashes, model ID,", "tokens, timestamps", "", "rule-based coding:",
         "feasibility, equity,", "rating and horizon", "breaches"], "run")
    box(ax, c4, 1.35, w, 1.05, "6  Historical check",
        ["5-year fund returns", "monthly-rebalanced mix", "worst 12-month loss vs", "stated loss tolerance"], "eval")
    box(ax, c4, 0.05, w, 1.15, "7  Analysis",
        ["RQ1 attribute weights", "RQ2 suitability breaches", "RQ3 BASE vs SUIT (paired)",
         "RQ4 consistency, probes", "RQ5 model differences"], "eval")
    arrow(ax, c1 + w, 1.85, c2, 1.85)
    arrow(ax, c1 + w, 0.6, c2, 0.6)
    arrow(ax, c2 + w, 1.6, c3, 1.6)
    arrow(ax, c2 + w, 0.75, c3, 0.75)
    arrow(ax, c3 + w, 1.6, c4, 1.75)
    arrow(ax, c3 + w, 0.75, c4, 0.6)
    arrow(ax, c4 + w / 2, 1.35, c4 + w / 2, 1.2)
    out = ROOT / "outputs" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "F00_design_pipeline.png", dpi=220, bbox_inches="tight")
    print("Wrote", out / "F00_design_pipeline.png")


if __name__ == "__main__":
    main()
