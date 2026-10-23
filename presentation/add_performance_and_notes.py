"""Post-process presentation.pptx (built by build_presentation.py on the course
template, which is not stored in the repository):

1. insert a results slide on performance and benchmarks after the RQ4 slide,
   reusing that slide's frame (kicker, title, logo, footer, page number) and
   its number panels; numbers come from outputs/tables (T28, T30, T32, T33)
   and the images from outputs/figures (F09, F10);
2. update the limitations panel on coding;
3. renumber the page numbers;
4. write speaker notes with a 25-minute timing plan on every slide.

Run after build_presentation.py:  python presentation/add_performance_and_notes.py
"""

import copy
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "presentation" / "presentation.pptx"
T = ROOT / "outputs" / "tables"


def title_of(slide) -> str:
    for sh in slide.shapes:
        if sh.has_text_frame and sh.top < Inches(0.3) and sh.left > Inches(1.0):
            return sh.text_frame.text.strip()
    return ""


def set_text(shape, value: str):
    """Replace the text but keep the formatting of the first run."""
    p = shape.text_frame.paragraphs[0]
    runs = p.runs
    runs[0].text = value
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    for extra in shape.text_frame.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)


def clone_frame(prs, src):
    """New slide after src with src's shapes except charts; pictures keep their images."""
    new = prs.slides.add_slide(src.slide_layout)
    for sh in list(new.shapes):
        sh._element.getparent().remove(sh._element)
    for sh in src.shapes:
        if sh.has_chart:
            continue
        el = copy.deepcopy(sh._element)
        for blip in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
            rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
            part = src.part.related_part(rid)
            blip.set("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed",
                     new.part.relate_to(part, RT.IMAGE))
        new.shapes._spTree.append(el)
    # move the new slide right after src
    lst = prs.slides._sldIdLst
    ids = list(lst)
    new_id = ids[-1]
    lst.remove(new_id)
    lst.insert(ids.index(next(i for i in ids if prs.slides.part.related_part(i.rId) is src.part)) + 1, new_id)
    return new


def fmt_range(lo, hi, digits=0, unit="%"):
    return f"{lo:.{digits}f}-{hi:.{digits}f}{unit}"


def performance_slide(prs, after):
    s = clone_frame(prs, after)
    t28 = pd.read_csv(T / "T28_ai_vs_benchmarks.csv")
    t30 = pd.read_csv(T / "T30_costs_by_risk_class.csv")
    t32 = pd.read_csv(T / "T32_return_by_rating_breach_c1_c2.csv")
    t33 = pd.read_csv(T / "T33_performance_summary.csv").set_index("portfolio")
    ai = t33.loc[[f"AI portfolios C{k}" for k in range(2, 6)]]
    agg = t33.loc[["AI portfolios C4", "AI portfolios C5"], "sharpe_above_model_pct"]
    c1 = t32[t32["risk_class"] == "C1"].set_index("rating_breach")["median_cagr_pct"]
    values = {
        "13": fmt_range(ai["sharpe_above_6040_pct"].min(), ai["sharpe_above_6040_pct"].max()),
        "14": "of AI portfolios for C2-C5 investors beat a 60/40 mix on the Sharpe ratio (60/40: 1.67% a year)",
        "15": fmt_range(agg.min(), agg.max()),
        "16": "of C4-C5 portfolios beat a rating-compliant model portfolio on Sharpe, helped by QDII funds",
        "17": f"{c1[True]:.2f}% vs {c1[False]:.2f}%",
        "18": "a year for C1 portfolios with vs without a non-permitted fund: the extra return breaks the rule",
        "19": f"{t30['max_cost_drag_bh_std_fee_exit_hi_pp'].max():.2f} pts",
        "20": "at most, return lost to fees a year (standard rates); ongoing fees already in NAV",
    }
    assert len(t28) and len(t33)
    for sh in list(s.shapes):
        name = sh.name.replace("TextBox ", "")
        if sh.has_text_frame and sh.top < Inches(0.3) and sh.left > Inches(1.0):
            set_text(sh, "PERFORMANCE AND BENCHMARKS (9.7)")
        elif sh.has_text_frame and Inches(0.3) <= sh.top < Inches(1.0) and sh.left > Inches(1.0):
            set_text(sh, "Good risk-adjusted returns, partly from breaking the rule")
        elif name in values:
            set_text(sh, values[name])
    s.shapes.add_picture(str(ROOT / "outputs" / "figures" / "F09_cumulative_growth_vs_benchmarks.png"),
                         Inches(1.15), Inches(1.35), height=Inches(2.7))
    s.shapes.add_picture(str(ROOT / "outputs" / "figures" / "F10_risk_return_vs_benchmarks.png"),
                         Inches(1.15), Inches(4.15), height=Inches(2.7))
    return s


NOTES = [
    ("0:00-0:45", "Title. We audited three Chinese chatbots as fund advisers: do they tailor advice to the client, "
     "is it suitable under China's rules, and does a suitability protocol in the prompt help?"),
    ("0:45-1:15", "Four parts: motivation, design, results, implications and limits."),
    ("1:15-1:30", "Part 1: why this needs an audit."),
    ("1:30-3:00", "A licensed distributor must classify the client C1-C5 and the product R1-R5 and may only sell at "
     "or below the client's class. A general-purpose chatbot has no such duty. Of the course's four dimensions - "
     "feasibility, suitability, fairness, performance - our primary focus is suitability; feasibility and performance "
     "are secondary, and fairness is excluded by design."),
    ("3:00-4:15", "Five questions and seven hypotheses, all fixed before any model was queried. Point to H4: risk "
     "tolerance should dominate, and H5: the protocol should cut breaches."),
    ("4:15-4:30", "Part 2: how we built the experiment."),
    ("4:30-6:00", "200 synthetic investors, one per cell of 5 horizons x 5 risk classes x 8 age bands, so the "
     "attributes are uncorrelated. Every investor goes to every model under both prompts: 1,200 main replies, plus "
     "repeats and single-attribute probes, 2,508 calls in total, all answered."),
    ("6:00-7:15", "Each profile covers the know-your-client items: age, income, goal, horizon, liquidity, experience, "
     "amount and risk tolerance. Show the example: a 21-year-old student with very high risk tolerance but a "
     "9-month horizon - a built-in conflict."),
    ("7:15-8:30", "23 real funds, verified against public records; ratings from Eastmoney because the course API has "
     "no rating field. No R5 fund, so only C1-C3 clients can break the rating rule."),
    ("8:30-9:45", "BASE is the adviser prompt with the rated menu; SUIT adds a four-step suitability protocol. BASE "
     "is an exact prefix of SUIT, so the protocol is the only difference."),
    ("9:45-11:00", "Every reply is scored mechanically: feasibility, rating breach, horizon cap, lock-up, loss "
     "tolerance against five years of NAV data, reliability, and - added after the main analysis - Sharpe, Calmar, "
     "benchmarks and fees. Effect sizes lead; p-values are Holm-adjusted."),
    ("11:00-11:15", "Part 3: results."),
    ("11:15-13:15", "Risk tolerance drives the portfolio: partial eta squared 0.66-0.83. Horizon works as a switch "
     "below one year. Age barely matters, against life-cycle theory."),
    ("13:15-15:45", "The key finding: although ratings are in the prompt, 82.5-85.8% of BASE replies to C1-C3 clients "
     "contain a fund above the ceiling, mostly bond funds for C1. Aggressive clients with 1-3 year horizons get about "
     "78% equity against a 30% cap. Losses beyond the stated limit were rare, but the window was benign for bonds."),
    ("15:45-18:00", "The protocol cuts rating breaches in every model, by 9.5, 11.1 and 24.5 points, and the models "
     "flag the conflict almost every time. But compliance does not follow: many clients the model classified "
     "correctly still get a fund above their class. Under SUIT the models differ; Kimi responds most."),
    ("18:00-19:30", "Same question three times: equity is stable, fund choices are not, and the breach verdict "
     "changes for up to 17.5% of clients. Probes: the stated horizon on its own moves equity only 1-4 points."),
    ("19:30-21:30", "Performance over Nov 2021 - Sep 2026, a weak period for Chinese equities. Most portfolios beat a "
     "60/40 mix on the Sharpe ratio, and aggressive clients' portfolios beat a rating-compliant model portfolio. "
     "For cautious clients the extra return came from non-permitted funds: performance and compliance pulled apart. "
     "Fees are negligible. The model portfolio is our stylised robo ladder, not a commercial robo record."),
    ("21:30-21:45", "Part 4: what follows."),
    ("21:45-23:15", "Limits: synthetic one-message clients, one shelf and date, a benign window, OpenRouter access with "
     "reasoning off, one wording, and the double coding of the conflict item is prepared but must be completed by "
     "two group members."),
    ("23:15-24:45", "Three takeaways: tailoring is one-dimensional; a rule in the prompt is not a control, so enforce "
     "suitability in code; audit with repeated queries."),
    ("24:45-25:00", "Thank you. Five minutes for questions."),
]


def main():
    prs = Presentation(str(DECK))
    slides = list(prs.slides)
    if any(title_of(s) == "PERFORMANCE AND BENCHMARKS (9.7)" for s in slides):
        raise SystemExit("Performance slide already present; rebuild the deck first.")
    rq4 = next(s for s in slides if title_of(s).startswith("RELIABILITY"))
    performance_slide(prs, rq4)

    for s in prs.slides:
        if title_of(s) == "LIMITATIONS":
            for sh in s.shapes:
                if sh.has_text_frame and sh.text_frame.text.startswith("Conflict acknowledgement awaits"):
                    set_text(sh, "Conflict item: two-coder sheets for all 1,199 replies prepared; coding and kappa "
                                 "pending.")

    slides = list(prs.slides)
    if len(slides) != len(NOTES):
        raise SystemExit(f"{len(slides)} slides but {len(NOTES)} notes")
    for i, (s, (clock, note)) in enumerate(zip(slides, NOTES), 1):
        for sh in s.shapes:
            if (sh.has_text_frame and sh.left >= Inches(11.5) and sh.top >= Inches(6.9)
                    and sh.text_frame.text.strip().isdigit()):
                set_text(sh, f"{i:02d}")
        s.notes_slide.notes_text_frame.text = f"[{clock}] {note}"
    prs.save(str(DECK))
    print(f"Saved {DECK}: {len(slides)} slides, 25-minute timing in the notes")


if __name__ == "__main__":
    main()
