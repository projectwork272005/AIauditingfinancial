"""Build presentation.pptx on the course template (SMBU class deck).

The template file supplies the slide master, theme, fonts, logo and campus
photographs; every slide is rebuilt for this project. Result slides draw
native PowerPoint charts from outputs/tables when the experiment has been run;
until then they carry an explicit "Results pending" panel and no numbers.

Usage:
  python presentation/build_presentation.py \
      [--template reference_materials/AI_Investment_Advisor_SMBU_Template.pptx] \
      [--outputs outputs] [--out presentation/presentation.pptx]
"""

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
NAVY, RED, GREY, INK = RGBColor(0x36, 0x5B, 0x7E), RGBColor(0xBE, 0x4D, 0x4C), RGBColor(0x7F, 0x8C, 0x99), RGBColor(0x4A, 0x4A, 0x4A)
PALE, PALE2, ICE, LINE, WHITE = (RGBColor(0xF2, 0xF6, 0xFA), RGBColor(0xE8, 0xEF, 0xF5), RGBColor(0xBA, 0xD0, 0xE4),
                                 RGBColor(0xDD, 0xE4, 0xEB), RGBColor(0xFF, 0xFF, 0xFF))
MODEL_RGB = [RGBColor(0x2C, 0x6A, 0xA8), RGBColor(0xBE, 0x4D, 0x4C), RGBColor(0x2A, 0x9D, 0x8F)]
FONT, FONT_ZH = "Calibri", "微软雅黑"
FOOTER = "Who Gets What? Auditing LLM Mutual Fund Advice"
MODEL_LABEL = {"doubao": "Doubao", "deepseek": "DeepSeek", "kimi": "Kimi", "glm": "GLM", "qwen": "Qwen", "gpt": "GPT-5 mini", "gemini": "Gemini"}


# ------------------------------------------------------------- primitives --

def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def text(slide, x, y, w, h, content, size=12, bold=False, color=INK, align=PP_ALIGN.LEFT, font=FONT,
         anchor=MSO_ANCHOR.TOP, spacing=None, name=None):
    """content: str or list of (str | list of (text, {bold, color, size}))."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        pieces = para if isinstance(para, list) else [(para, {})]
        for chunk, opt in pieces:
            r = p.add_run()
            r.text = chunk
            r.font.name = opt.get("font", font)
            r.font.size = Pt(opt.get("size", size))
            r.font.bold = opt.get("bold", bold)
            r.font.color.rgb = opt.get("color", color)
    return tb


def bullets(slide, x, y, w, h, items, size=13, gap=8):
    paras = []
    for it in items:
        if isinstance(it, tuple):
            head, rest = it
            paras.append([("■  ", {"color": RED, "size": size - 3}), (head, {"bold": True, "color": NAVY}),
                          (rest, {})])
        else:
            paras.append([("■  ", {"color": RED, "size": size - 3}), (it, {})])
    return text(slide, x, y, w, h, paras, size=size, spacing=gap)


# ---------------------------------------------------------------- frames --

class Deck:
    def __init__(self, template: Path):
        self.prs = Presentation(str(template))
        with zipfile.ZipFile(template) as z:
            self.media = {n.split("/")[-1]: z.read(n) for n in z.namelist() if n.startswith("ppt/media/")}
        self.media["design.png"] = (ROOT / "outputs" / "figures" / "F00_design_pipeline.png").read_bytes()
        lst = self.prs.slides._sldIdLst
        for sld in list(lst):
            self.prs.part.drop_rel(sld.rId)
            lst.remove(sld)
        self.blank = next(l for l in self.prs.slide_layouts if len(l.placeholders) == 0)
        self.n = 0

    def img(self, slide, name, x, y, w=None, h=None):
        kw = {}
        if w:
            kw["width"] = Inches(w)
        if h:
            kw["height"] = Inches(h)
        return slide.shapes.add_picture(io.BytesIO(self.media[name]), Inches(x), Inches(y), **kw)

    def new(self, notes=None):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        if notes:
            s.notes_slide.notes_text_frame.text = notes
        return s

    def content(self, kicker, title, notes=None):
        s = self.new(notes)
        rect(s, 0.55, 0.0, 0.12, 0.58, RED)
        rect(s, 0.72, 0.26, 0.12, 0.32, ICE)
        text(s, 1.05, 0.13, 8.0, 0.24, kicker.upper(), size=9.5, bold=True, color=RED)
        text(s, 1.05, 0.36, 8.6, 0.66, title, size=22, bold=True, color=NAVY)
        self.img(s, "image3.png", 9.83, 0.09, w=2.95)
        rect(s, 0.55, 1.20, 12.23, 0.012, ICE)
        rect(s, 0.55, 6.95, 12.23, 0.012, LINE)
        text(s, 0.55, 7.02, 8.6, 0.26, FOOTER, size=8.5, color=GREY)
        text(s, 11.55, 7.0, 1.23, 0.28, f"{self.n:02d}", size=10.5, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
        return s

    def section(self, part, title, zh, lead, points, photo, notes=None):
        s = self.new(notes)
        self.img(s, photo, 0.0, 0.0, w=4.95, h=7.5)
        rect(s, 0.0, 2.86, 5.95, 1.92, NAVY)
        text(s, 0.72, 3.0, 4.8, 0.9, f"PART {part:02d}", size=44, bold=True, color=WHITE)
        rect(s, 0.75, 3.98, 2.6, 0.03, ICE)
        text(s, 0.75, 4.12, 4.6, 0.3, "S M B U   ·   F I N T E C H", size=8.5, color=ICE)
        text(s, 6.45, 2.62, 6.1, 0.3, f"SECTION {part:02d}", size=10, bold=True, color=RED)
        text(s, 6.45, 2.95, 6.3, 1.15, title, size=31, bold=True, color=NAVY)
        text(s, 6.48, 4.05, 6.2, 0.3, zh, size=12, color=GREY, font=FONT_ZH)
        rect(s, 6.48, 4.45, 1.4, 0.04, RED)
        text(s, 6.48, 4.66, 6.2, 0.5, lead, size=12.5)
        for i, ptxt in enumerate(points):
            rect(s, 6.48, 5.42 + 0.42 * i, 0.09, 0.09, RED)
            text(s, 6.72, 5.32 + 0.42 * i, 5.9, 0.32, ptxt, size=11.5)
        text(s, 11.55, 7.0, 1.23, 0.28, f"{self.n:02d}", size=10.5, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)
        return s


def pending_panel(slide, x, y, w, h, what):
    rect(slide, x, y, w, h, PALE)
    rect(slide, x, y, 0.06, h, GREY)
    text(slide, x + 0.3, y + 0.25, w - 0.5, h - 0.5,
         [[("Results pending", {"bold": True, "color": NAVY, "size": 16})],
          [(what, {"size": 12.5})],
          [("This slide is generated from outputs/tables after the experiment has been run; "
            "no number is shown before then.", {"size": 11, "color": GREY})]], spacing=10)


def card(slide, x, y, w, h, head, head_fill, title, body):
    rect(slide, x, y, w, h, PALE)
    hd = rect(slide, x, y, w, 0.55, head_fill)
    tf = hd.text_frame
    tf.margin_left = Inches(0.2)
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = head
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(13.5), True, WHITE, FONT
    top = y + 0.7
    if title:
        text(slide, x + 0.2, top, w - 0.4, 0.6, title, size=13, bold=True, color=NAVY)
        top += 0.65
    text(slide, x + 0.2, top, w - 0.4, h - (top - y) - 0.15, body, size=11.5)


def stat(slide, x, y, w, value, label):
    rect(slide, x, y, w, 1.15, PALE)
    text(slide, x + 0.15, y + 0.08, w - 0.3, 0.6, value, size=28, bold=True, color=NAVY)
    text(slide, x + 0.15, y + 0.72, w - 0.3, 0.38, label, size=11, color=GREY)


def style_chart(chart, colors, title=None, legend=True, y_max=None, y_title=None):
    chart.font.name, chart.font.size = FONT, Pt(10)
    chart.font.color.rgb = INK
    chart.has_title = bool(title)
    if title:
        chart.chart_title.text_frame.text = title
        chart.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
        chart.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(9)
    va = chart.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = LINE
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(9)
    va.tick_labels.font.color.rgb = GREY
    if y_max is not None:
        va.maximum_scale, va.minimum_scale = y_max, 0
    if y_title:
        va.has_title = True
        va.axis_title.text_frame.text = y_title
        va.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    ca = chart.category_axis
    ca.tick_labels.font.size = Pt(9)
    ca.tick_labels.font.color.rgb = GREY
    ca.format.line.color.rgb = LINE
    for ser, col in zip(chart.plots[0].series, colors):
        fmt = ser.format
        if chart.chart_type in (XL_CHART_TYPE.LINE_MARKERS, XL_CHART_TYPE.LINE):
            fmt.line.color.rgb = col
            fmt.line.width = Pt(2)
            ser.smooth = False
        else:
            fmt.fill.solid()
            fmt.fill.fore_color.rgb = col


def lighten(c: RGBColor, f=0.55) -> RGBColor:
    return RGBColor(*(int(v + (255 - v) * f) for v in (c[0], c[1], c[2])))


# ----------------------------------------------------------------- slides --

def build(template: Path, outputs: Path, out: Path):
    d = Deck(template)
    tables = outputs / "tables"
    have = (outputs / "experiment_results.csv").exists() and (tables / "T05_equity_by_risk_class.csv").exists()

    # 1 title
    s = d.new("Title. One audit, three questions: does LLM fund advice follow the investor, is it suitable, "
              "and does a prompt-level suitability protocol help?")
    d.img(s, "image4.png", 8.15, 0.0, w=5.18, h=7.5)
    rect(s, 8.15, 0.0, 0.06, 7.5, RED)
    d.img(s, "image3.png", 0.85, 0.62, w=3.05)
    text(s, 0.85, 1.86, 6.9, 0.26, "FINTECH  ·  THEORY & PRACTICE", size=10.5, bold=True, color=RED)
    text(s, 0.85, 2.2, 7.0, 1.55, ["Who Gets What?", "Auditing LLM Mutual Fund Advice"], size=32, bold=True, color=NAVY)
    text(s, 0.85, 3.72, 7.0, 0.45, "Age, risk tolerance, horizon and a suitability protocol", size=17, color=NAVY)
    rect(s, 0.85, 4.32, 1.55, 0.04, RED)
    for i, (lab, w) in enumerate((("Responsiveness", 1.75), ("Suitability", 1.45), ("Guardrail", 1.35),
                                  ("Reliability", 1.4))):
        x = 0.85 + sum((1.75, 1.45, 1.35, 1.4)[:i]) + 0.12 * i
        b = rect(s, x, 4.56, w, 0.38, PALE, MSO_SHAPE.ROUNDED_RECTANGLE)
        b.text_frame.text = lab
        para = b.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        para.runs[0].font.size, para.runs[0].font.bold = Pt(10.5), True
        para.runs[0].font.color.rgb, para.runs[0].font.name = NAVY, FONT
    text(s, 0.85, 5.4, 7.1, 0.95, ["200 synthetic investors (5 horizons x 5 risk classes x 8 age bands)",
                                   "x 2 prompts x 3 LLMs, 23 verified Chinese funds, 5-year historical check"],
         size=12)
    rect(s, 0.85, 6.52, 6.4, 0.012, LINE)
    text(s, 0.85, 6.63, 7.1, 0.3, "Shenzhen MSU-BIT University  ·  Group project  ·  2026", size=9.5, color=GREY)

    # 2 contents
    s = d.new("Agenda.")
    d.img(s, "image5.png", 0.0, 0.0, w=4.6, h=7.5)
    rect(s, 0.0, 2.75, 4.6, 1.75, NAVY)  # solid band so the white title reads on the photo
    text(s, 0.55, 3.0, 3.6, 0.9, "Contents", size=36, bold=True, color=WHITE)
    text(s, 0.58, 3.85, 3.6, 0.4, "目录", size=16, color=WHITE, font=FONT_ZH)
    items = [("Motivation & Questions", "研究动机与问题"),
             ("Design & Method", "实验设计与方法"),
             ("Results", "实验结果"),
             ("Implications & Limits", "启示与局限")]
    for i, (en, zh) in enumerate(items):
        y = 1.3 + i * 1.25
        text(s, 5.4, y, 0.9, 0.6, f"{i + 1:02d}", size=26, bold=True, color=RED if i % 2 == 0 else NAVY)
        text(s, 6.5, y + 0.02, 5.8, 0.4, en, size=17, bold=True, color=NAVY)
        text(s, 6.5, y + 0.45, 5.8, 0.3, zh, size=11, color=GREY, font=FONT_ZH)
        rect(s, 6.5, y + 0.9, 5.9, 0.01, LINE)

    # 3 section 1
    d.section(1, "Motivation & Questions", "研究动机与问题",
              "Chatbots now give fund advice, but carry no suitability duty.",
              ["What China's suitability rule requires", "Five research questions"], "image2.png")

    # 4 motivation
    s = d.content("Why audit", "A chatbot advises; a distributor must match risk",
                  "A licensed distributor classifies the client C1-C5 and the product R1-R5 and may only sell "
                  "products at or below the client's class. A general-purpose model has no such duty.")
    card(s, 0.55, 1.5, 5.9, 3.0, "Licensed fund distributor", NAVY, "Suitability is mandatory",
         "Collects horizon, goals and risk tolerance; classifies client C1-C5 and product R1-R5; sells only "
         "products rated at or below the client's class (CSRC Measures; AMAC 2017 guideline).")
    card(s, 6.88, 1.5, 5.9, 3.0, "General-purpose LLM", RED, "Suitability is optional",
         "Answers any request fluently; no questionnaire, product database or check unless the deployer adds one. "
         "Earlier audits: advice keys mainly on stated risk tolerance (Ross & Lo, 2026).")
    text(s, 0.55, 4.75, 12.2, 0.35, "The matching ceiling used to score every recommendation", size=12, bold=True,
         color=NAVY)
    for i in range(5):
        x = 0.55 + i * 2.46
        b = rect(s, x, 5.15, 2.3, 0.62, [PALE2, ICE, RGBColor(0x9C, 0xBA, 0xD4), RGBColor(0x5F, 0x84, 0xA8), NAVY][i])
        text(s, x + 0.12, 5.2, 2.1, 0.52, [[(f"C{i + 1}", {"bold": True, "size": 14,
                                                         "color": WHITE if i >= 3 else NAVY}),
                                          (f"  may hold R1-R{i + 1}" if i else "  may hold R1 only",
                                           {"size": 11, "color": WHITE if i >= 3 else INK})]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, 0.55, 5.95, 12.2, 0.8, "Gap: no audit yet combines an orthogonal attribute design, a real regulatory "
         "rule with real product ratings, a prompt-level guardrail test and a historical check of each portfolio.",
         size=12)

    # 5 research questions
    s = d.content("Research questions", "Five questions, fixed before any model was queried",
                  "RQ1-RQ5 and hypotheses H1-H7 are pre-specified in research_design.md.")
    qs = [("RQ1 Responsiveness", NAVY, "How much weight do risk, horizon and age carry?",
           "H1-H4: risk up, horizon up, age down; risk tolerance dominates."),
          ("RQ2 Suitability", RED, "How often are rules breached?",
           "Rating ceiling, horizon cap, 3-year lock-up, stated loss vs history. H6: conflicts breach most."),
          ("RQ3 Guardrail", GREY, "Does a suitability protocol help?",
           "BASE vs SUIT within investor. H5: fewer rating breaches."),
          ("RQ4-5 Reliability & models", NAVY, "Stable? Model-specific?",
           "Repeats, one-attribute probes, three developers. H7: stable equity, varying funds.")]
    for i, (h, c, t, b) in enumerate(qs):
        card(s, 0.55 + i * 3.08, 1.5, 2.92, 3.6, h, c, t, b)
    rect(s, 0.55, 5.4, 12.23, 1.2, PALE2)
    rect(s, 0.55, 5.4, 0.06, 1.2, RED)
    text(s, 0.9, 5.55, 11.7, 0.9, [[("Approach: ", {"bold": True, "color": NAVY}),
                                    ("treat each model as a candidate adviser on a fund platform, give it the same "
                                     "synthetic clients and the same verified shelf, and score what it recommends "
                                     "against rules and data rather than intuition.", {})]], size=12.5)

    # 6 section 2
    d.section(2, "Design & Method", "实验设计与方法",
              "A balanced factorial of synthetic clients, a verified shelf, two prompts.",
              ["200 investors, 23 funds, 3 models", "Coding, back-test and statistics"], "image5.png")

    # 7 design
    s = d.content("Experimental design", "One investor per cell, every model, both prompts",
                  "Repeated-measures design: 200 unique investors; condition and model vary within investor.")
    for i, (v, lab) in enumerate((("200", "unique synthetic investors"), ("2", "prompt conditions"),
                                  ("3", "LLMs: Doubao, DeepSeek, Kimi"), ("2,508", "planned API calls"))):
        stat(s, 0.55 + i * 1.62, 1.5, 1.5, v, lab)
    bullets(s, 0.55, 2.9, 6.3, 3.8, [
        ("Full factorial: ", "5 horizons x 5 risk classes x 8 age bands; attributes uncorrelated (Cramer's V = 0)."),
        ("Within investor: ", "2 prompts x 3 models = 1,200 main observations, all paired."),
        ("Consistency: ", "40 investors asked twice more (480 calls)."),
        ("Probes: ", "10 anchors, one attribute changed at a time (828 calls)."),
        ("Controls: ", "same wording, menu, order, temperature 0.7; random call order."),
    ], size=12.5)
    d.img(s, "design.png", 7.05, 1.5, w=5.73)

    # 8 investor profiles
    s = d.content("Synthetic investors", "Three attributes, defined before generation",
                  "Every class is defined on the same criteria; the class code is never shown to the model.")
    rows = [("Horizon", "H1 <1 yr  ·  H2 1-3  ·  H3 3-5  ·  H4 5-10  ·  H5 10+ yrs"),
            ("Risk tolerance", "C1 no loss  ·  C2 ~5%  ·  C3 ~15%  ·  C4 ~25%  ·  C5 40%+ one-year decline"),
            ("Age", "18-24 · 25-34 · 35-44 · 45-54 · 55-59 · 60-64 · 65-74 · 75-85")]
    for i, (k, v) in enumerate(rows):
        y = 1.5 + i * 0.78
        rect(s, 0.55, y, 1.9, 0.62, NAVY)
        text(s, 0.65, y, 1.75, 0.62, k, size=13, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        rect(s, 2.45, y, 4.6, 0.62, PALE)
        text(s, 2.6, y, 4.4, 0.62, v, size=11, anchor=MSO_ANCHOR.MIDDLE)
    bullets(s, 0.55, 4.0, 6.5, 2.7, [
        ("Consistent: ", "employment, objective, experience and liquidity follow age and horizon by rule."),
        ("Validated: ", "16 independent checks, all pass."),
        ("Synthetic: ", "no real person is described; no gender or name signals."),
    ], size=12.5)
    prof = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    ex = prof[(prof.risk_class == "C5") & (prof.horizon_band == "H1") & (prof.age_band == "A1")].iloc[0]
    rect(s, 7.35, 1.5, 5.43, 5.2, PALE2)
    text(s, 7.55, 1.6, 5.0, 0.3, f"ONE PROFILE AS THE MODEL SEES IT ({ex.investor_id}, a built-in conflict)",
         size=9.5, bold=True, color=RED)
    text(s, 7.55, 1.95, 5.05, 4.7, ex.profile_text.split("\n"), size=10.5, spacing=3)

    # 9 fund menu
    s = d.content("Fund menu", "23 real Chinese funds, verified before use",
                  "Identity checked against two public records per fund; ratings and histories from one source.")
    menu = pd.read_csv(ROOT / "data" / "fund_menu_candidates.csv", dtype=str)
    counts = menu["asset_class"].value_counts().reindex(["Cash", "Bond", "Hybrid", "Equity", "Commodity"])
    cd = CategoryChartData()
    cd.categories = list(counts.index)
    cd.add_series("Funds", [int(v) for v in counts.values])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.55), Inches(1.45), Inches(5.6), Inches(3.4), cd)
    ch = gf.chart
    style_chart(ch, [NAVY], title="Funds by asset class", legend=False)
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.font.size = Pt(10)
    ch.plots[0].gap_width = 80
    ch.category_axis.reverse_order = True
    bullets(s, 6.55, 1.5, 6.2, 5.2, [
        ("14 managers, ", "none with more than 3 funds."),
        ("4 QDII funds: ", "overseas equity inside the R1-R5 system (Nasdaq-100, S&P 500, Hang Seng, global oil)."),
        ("Liquidity test: ", "a pension FOF with a 3-year minimum holding period."),
        ("Domestic only: ", "mainland investors cannot buy foreign-domiciled funds directly."),
        ("Not trusted blindly: ", "ratings change; one manager re-rated 20+ funds in August 2026."),
    ], size=12.5)

    # 10 prompts
    s = d.content("Prompt conditions", "BASE vs SUIT: the protocol is the only difference",
                  "BASE is an exact prefix of SUIT, checked by an automated test.")
    card(s, 0.55, 1.5, 5.9, 4.0, "BASE  ·  adviser prompt", NAVY, "Role + menu with ratings + JSON format",
         "\"You are an AI investment adviser deployed on a licensed mutual fund distribution platform... You may "
         "recommend only funds from the platform's fund menu below...\" Ratings are visible, so a breach cannot be "
         "blamed on missing information.")
    card(s, 6.88, 1.5, 5.9, 4.0, "SUIT  ·  BASE + suitability protocol", RED, "Four mandatory steps",
         "1 Classify the client C1-C5.  2 Use only funds rated at or below that class.  3 Check horizon, liquidity "
         "and holding periods.  4 State and resolve conflicts. Adds three JSON keys: class, check, conflicts.")
    rect(s, 0.55, 5.75, 12.23, 0.9, PALE2)
    text(s, 0.85, 5.85, 11.8, 0.7, [[("Held constant: ", {"bold": True, "color": NAVY}),
                                     ("investor text, menu and order, output format, temperature 0.7, token limit, "
                                      "random call order. Every prompt is hashed in the raw log.", {})]], size=12)

    # 11 evaluation
    s = d.content("Evaluation framework", "Scored against rules and data, not intuition",
                  "Effect sizes lead; p-values are Holm-adjusted.")
    metrics = [("Feasibility", "parse, off-menu codes, weights sum to 100"),
               ("Responsiveness", "equity and weighted risk vs each attribute; partial eta squared"),
               ("Rating breach", "any fund above the client's R ceiling"),
               ("Horizon / lock-up", "equity above horizon cap; 3-year fund for short horizons"),
               ("Loss tolerance", "worst 12-month return 2021-26 vs stated maximum loss"),
               ("Reliability", "ICC over 3 repeats; Jaccard of fund sets; probe slopes")]
    for i, (k, v) in enumerate(metrics):
        x, y = 0.55 + (i % 2) * 6.17, 1.5 + (i // 2) * 1.05
        rect(s, x, y, 6.0, 0.9, PALE)
        rect(s, x, y, 0.06, 0.9, [NAVY, RED][i % 2])
        text(s, x + 0.25, y + 0.08, 5.6, 0.75, [[(k, {"bold": True, "color": NAVY, "size": 13})], [(v, {"size": 11.5})]])
    text(s, 0.55, 4.75, 12.2, 1.9, [[("Tests: ", {"bold": True, "color": NAVY}),
                                     ("Spearman and Type II ANOVA per model x prompt; McNemar and Wilcoxon for paired "
                                      "BASE vs SUIT; Friedman and Cochran's Q across models; ICC(1,1) for repeats. "
                                      "With 200 paired investors, effects of d = 0.2 are detectable, so "
                                      "interpretation rests on effect sizes.", {})]], size=12.5)

    # 12 section 3
    d.section(3, "Results", "实验结果",
              "What the models recommended, and how suitable it was.",
              ["Responsiveness and suitability", "Guardrail, reliability, models"], "image4.png")

    # 13-16 result slides
    res_slides = [
        ("Responsiveness", "How portfolios follow risk, horizon and age", "T05_equity_by_risk_class.csv",
         "Mean equity exposure by risk class, per model and prompt (Figures 2-4, Table 11)."),
        ("Suitability", "Where recommendations breach the rules", "T12_suitability_by_risk_class.csv",
         "Rating-ceiling breaches by risk class, horizon and lock-up breaches, loss-tolerance check."),
        ("Guardrail and models", "Does the suitability protocol change the advice?", "T13_condition_effects_paired.csv",
         "Paired BASE vs SUIT differences per model; model comparison."),
        ("Reliability", "Repeats and one-attribute probes", "T15_consistency_repeated_queries.csv",
         "ICC of equity over three repeats; probe slopes per attribute."),
    ]
    for kicker, title, table_name, what in res_slides:
        s = d.content(kicker, title)
        if have and table_name == "T05_equity_by_risk_class.csv":
            t = pd.read_csv(tables / table_name)
            cats = ["C1", "C2", "C3", "C4", "C5"]
            cd = CategoryChartData()
            cd.categories = cats
            cols = []
            for i, mk in enumerate(sorted(t["model_key"].unique())):
                for cond in ("BASE", "SUIT"):
                    g = t[(t.model_key == mk) & (t.condition == cond)].set_index("risk_class").reindex(cats)
                    cd.add_series(f"{MODEL_LABEL.get(mk, mk)} {cond}",
                                  [None if pd.isna(v) else round(float(v), 1) for v in g["mean"]])
                    cols.append(lighten(MODEL_RGB[i % 3]) if cond == "BASE" else MODEL_RGB[i % 3])
            gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(0.55), Inches(1.4), Inches(7.6), Inches(5.3), cd)
            style_chart(gf.chart, cols, title="Mean equity exposure (%) by risk class", y_max=100)
            pending_panel(s, 8.4, 1.5, 4.38, 3.0, "Interpretation is written from the analysis tables.")
        else:
            pending_panel(s, 0.55, 1.6, 12.23, 4.8, what)

    # 17 section 4
    d.section(4, "Implications & Limits", "启示与局限",
              "What a platform deploying an LLM adviser should take away.",
              ["Implications", "Limitations and next steps"], "image2.png")

    # 18 limitations
    s = d.content("Limitations", "What this design can and cannot show")
    for i, (h, b) in enumerate([
            ("Synthetic clients", "Clear, template-written profiles: close to a best case for tailoring."),
            ("One shelf, one window", "23 funds, ratings on one date, five years of history; past is not future."),
            ("Model drift", "Hosted models change; returned model IDs and repeat variation are recorded."),
            ("One wording", "One protocol and menu order; prompt format matters (Sclar et al., 2024)."),
            ("Judgement in caps", "Equity caps are our operationalisation; the rating rule is external."),
            ("Keyword coding", "Conflict acknowledgement awaits manual validation (two coders, kappa).")]):
        x, y = 0.55 + (i % 3) * 4.1, 1.5 + (i // 3) * 2.55
        card(s, x, y, 3.95, 2.35, f"{i + 1:02d}  {h}", [NAVY, RED, GREY][i % 3], "", b)

    # 19 takeaways
    s = d.content("Takeaways", "Conclusions")
    pending_panel(s, 0.55, 1.6, 12.23, 4.8, "Three takeaways, one per question group, written from the results.")

    # 20 thanks
    s = d.new()
    d.img(s, "image13.png", 6.6, 0.0, h=7.5)
    rect(s, 0.0, 0.0, 6.6, 7.5, NAVY)
    rect(s, 6.6, 0.0, 0.06, 7.5, RED)
    rect(s, 0.8, 0.8, 3.4, 0.95, WHITE)  # white backing so the logo reads on navy
    d.img(s, "image3.png", 0.92, 0.92, w=3.15)
    text(s, 0.8, 2.6, 5.6, 0.9, "谢谢观看", size=40, bold=True, color=WHITE, font=FONT_ZH)
    text(s, 0.82, 3.5, 5.6, 0.4, "T H A N K   Y O U", size=12, color=ICE)
    text(s, 0.82, 4.6, 5.6, 1.2, ["Who Gets What? Auditing LLM Mutual Fund Advice",
                                  "Responsiveness  ·  Suitability  ·  Guardrail  ·  Reliability"],
         size=12, color=WHITE, spacing=6)
    text(s, 0.82, 6.4, 5.6, 0.6, ["FinTech: Theory & Practice", "Shenzhen MSU-BIT University"], size=10, color=ICE)

    d.prs.save(str(out))
    print(f"Wrote {out} ({d.n} slides; results {'included' if have else 'pending'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default=str(ROOT / "reference_materials" / "AI_Investment_Advisor_SMBU_Template.pptx"))
    ap.add_argument("--outputs", default=str(ROOT / "outputs"))
    ap.add_argument("--out", default=str(ROOT / "presentation" / "presentation.pptx"))
    a = ap.parse_args()
    build(Path(a.template), Path(a.outputs), Path(a.out))


if __name__ == "__main__":
    main()
