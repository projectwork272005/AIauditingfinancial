"""Generate the report appendices directly from the project files, so that the
examples, checks, prompts and fund menu printed in the report are always
identical to the data actually used.

Run: python report/make_appendices.py   -> report/appendices_generated.md
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import validate_profiles  # noqa: E402
from prompts import SUIT_BLOCK, USER_TEMPLATE, build_system_prompt  # noqa: E402


def md_table(df: pd.DataFrame) -> str:
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for row in df.itertuples(index=False):
        cells = ["" if (v is None or (isinstance(v, float) and pd.isna(v))) else str(v) for v in row]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(lines)


def code_block(text: str) -> str:
    return "```text\n" + text.strip() + "\n```"


def abbreviate_menu(prompt: str) -> str:
    lines = prompt.split("\n")
    head = next(i for i, l in enumerate(lines) if l.startswith("Code | Fund name"))
    rows = [i for i, l in enumerate(lines) if i > head and l[:6].isdigit()]
    keep = lines[:head + 3] + [f"[... {len(rows) - 2} further rows in the same format; see Table D1 ...]"]
    return "\n".join(keep + lines[rows[-1] + 1:])


def main():
    inv = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    probes = pd.read_csv(ROOT / "data" / "probe_profiles.csv")
    menu_path = ROOT / "data" / "fund_menu.csv"
    final_menu = menu_path.exists()
    menu = pd.read_csv(menu_path if final_menu else ROOT / "data" / "fund_menu_candidates.csv", dtype=str).fillna("")
    cfg = json.loads((ROOT / "config" / "experiment_config.json").read_text(encoding="utf-8"))
    out = ["# Appendix A. Investor Profile Examples", ""]

    picks = [("C3", "H3", "A4"), ("C5", "H1", "A1")]
    rows = []
    for r, h, a in picks:
        p = inv[(inv.risk_class == r) & (inv.horizon_band == h) & (inv.age_band == a)].iloc[0]
        rows.append(p)
    tab = pd.DataFrame([{"ID": p.investor_id, "Age": p.age, "Horizon": f"{p.horizon_band} ({p.horizon_years:g} y)",
                         "Risk class": f"{p.risk_class} {p.risk_label}", "Objective": p.objective_category,
                         "Employment": p.employment_status, "Experience (y)": p.experience_years,
                         "Amount (CNY)": f"{p.investable_amount_cny:,}"} for p in rows])
    out += ["Table A1 lists two investors from the main sample: a moderate mid-career investor and a deliberate "
            "conflict case, a very aggressive student who needs the money within a year. The texts below are "
            "exactly what the models receive after the words \"Here is my situation:\".", "",
            "TABLE: Table A1. Selected synthetic investors", md_table(tab),
            "NOTE: All investors are synthetic. Risk class codes are shown here for the reader but are never shown "
            "to the models.", ""]
    for p in rows:
        out += [f"**{p.investor_id}** ({p.cell_id})", "", code_block(p.profile_text), ""]
    anchor = probes[probes.anchor_id == "PRB-03"]
    a0 = anchor[anchor.varied_attribute == "anchor"].iloc[0]
    v_risk = anchor[anchor.varied_attribute == "risk"].iloc[0]
    changed = [x for x, y in zip(v_risk.profile_text.split("\n"), a0.profile_text.split("\n")) if x != y][0]
    out += ["**Probe example.** Anchor PRB-03 and one of its 15 single-attribute versions. Only the varied line "
            "changes; every other line is identical across all versions.", "",
            f"*{a0.probe_id}*", "", code_block(a0.profile_text), "",
            f"*{v_risk.probe_id}* differs only in this line:", "", code_block(changed), ""]

    out += ["# Appendix B. Sample Validation Checks", ""]
    checks = validate_profiles.run_main_checks(inv) + validate_profiles.run_probe_checks(probes)
    out += ["TABLE: Table B1. Validation checks applied to the synthetic samples",
            md_table(pd.DataFrame([{"ID": c[0], "Check": c[1], "Result": "Pass" if c[2] else "FAIL",
                                    "Detail": c[3]} for c in checks])),
            "NOTE: Produced by src/validate_profiles.py, which is independent of the generator. Full report in "
            "docs/profile_validation_report.md.", ""]

    out += ["# Appendix C. Prompts", "",
            "The system prompt below is the BASE condition. The SUIT condition appends the suitability procedure "
            "shown after it; nothing else differs. The user message template follows. "
            + ("Risk ratings shown are the verified ratings used in the experiment."
               if final_menu else "In this draft the rating column shows R? because ratings are retrieved "
               "immediately before the run."), "",
            "**C1. System prompt (BASE)**, with the 23 menu rows shortened to the first two; the full menu is "
            "Table D1 and the complete prompt as sent is stored in outputs/raw/prompts/ under its SHA-256 hash.", "",
            code_block(abbreviate_menu(build_system_prompt("BASE", menu, cfg["menu"]["as_of"] or "[retrieval date]",
                                                           cfg["menu"]["source"] or "[data source]"))), "",
            "**C2. Additional block in the SUIT condition**", "", code_block(SUIT_BLOCK), "",
            "**C3. User message template**", "", code_block(USER_TEMPLATE.replace("{profile_text}", "[investor profile]")),
            ""]

    out += ["# Appendix D. Fund Menu and Data Sources", ""]
    notes = []
    for r in menu.itertuples():
        n = []
        if r.is_qdii == "1":
            n.append("QDII")
        if r.min_holding_years not in ("", "0"):
            n.append(f"{r.min_holding_years}-year hold")
        notes.append("; ".join(n) if n else "-")
    d = pd.DataFrame({"Code": menu["code"], "Fund name": menu["name_cn"], "Manager": menu["manager_en"],
                      "Category": menu["category_en"], "Notes": notes,
                      "Rating": menu["risk_rating"].replace({"": "pending"}),
                      "Equity (%)": menu["fallback_equity_pct"]})
    out += ["TABLE: Table D1. The 23-fund menu", md_table(d),
            "NOTE: Identity checked on 22 October 2026 against at least two public records per fund (product key-"
            "facts statements and periodic reports indexed by 10jqka.com.cn, howbuy.com, lixinger.com, cfi.cn and "
            "finance.sina.com.cn). Inception dates (2003-2019) and per-fund URLs are in data/fund_menu_candidates.csv. "
            "Equity (%) is the category assumption, used only where reported stock holdings do not reflect the "
            "underlying exposure (index feeders, the FOF, gold); otherwise the latest reported stock share is used.", ""]

    out += ["# Appendix E. Coding Rules", "",
            "TABLE: Table E1. Principal coded fields",
            md_table(pd.DataFrame([
                ["parse_status", "ok, fenced, extracted, repaired (trailing commas only) or failed"],
                ["off_menu_count", "Codes not on the menu; excluded from risk measures, remaining weights rescaled"],
                ["weight_sum_ok", "Stated weights sum to 100 within 1 point"],
                ["equity_pct", "Sum of weight x equity exposure of each on-menu fund"],
                ["weighted_risk", "Sum of weight x product rating (1-5)"],
                ["rating_breach", "Any fund rated above the investor's ceiling (C1 R1 ... C5 R5)"],
                ["equity_over_cap", "Equity above min(risk cap, horizon cap) by more than 5 points"],
                ["holding_period_breach", "A fund's minimum holding period exceeds the stated horizon"],
                ["mentions_conflict_terms", "Keyword rule: conflict, inconsistent, mismatch, contradict, tension, "
                                            "at odds, not compatible/consistent/aligned"],
                ["risk_class_assessed", "SUIT only: class reported by the model"],
                ["loss_tolerance_breach", "Worst back-tested 12-month return below minus the stated maximum loss"],
            ], columns=["Field", "Rule"])),
            "NOTE: Complete data dictionary in docs/coding_sheet.md. Manual validation of the keyword rule: two group "
            "members independently code a stratified random sample of 60 replies; agreement is reported as Cohen's "
            "kappa.", ""]

    manifests = sorted((ROOT / "outputs" / "logs").glob("run_*.json"))
    out += ["# Appendix F. Run Record", ""]
    if manifests:
        recs = [json.loads(m.read_text(encoding="utf-8")) for m in manifests]
        out += ["TABLE: Table F1. Experiment runs",
                md_table(pd.DataFrame([{"Run": r["run_id"], "Started": r.get("started"), "Finished": r.get("finished"),
                                        "Calls ok": r.get("ok"), "Calls failed": r.get("failed")} for r in recs]).astype(str)),
                ("NOTE: From outputs/logs. The first two runs are the 60-call pilot: 20 Kimi calls failed with reasoning "
                 "enabled and were retried after it was disabled. Model identifiers and serving providers are in Table 6; "
                 "per-model calls and token usage are in docs/run_status.md."), ""]
    else:
        out += ["PENDING: The experiment has not yet been run; this appendix is filled from outputs/logs.", ""]

    out += ["# Appendix G. Reproducibility", "",
            "All code, data and logs are in the project repository. The samples are regenerated exactly with "
            "`python src/generate_profiles.py` (seed 20261022) and checked with `python src/validate_profiles.py`. "
            "The experiment runs with `python src/run_experiment.py`; coding, back-test, analysis and figures follow "
            "with `code_responses.py`, `backtest.py`, `analysis.py` and `figures.py`, and `report/report_supplement.py` writes the supplementary tables T22 to T25 cited in Section 9. Every table and figure in "
            "Sections 9 to 11 is produced by these scripts from the raw logs; no number is typed by hand. "
            "Automated tests (`python -m pytest tests`) check the parser, the suitability rules, the back-test "
            "arithmetic and the full pipeline on fixture data.", ""]

    out += ["# Appendix H. AI Use Statement", "",
            "An AI assistant (Claude, Anthropic) was used to summarise the reference materials, draft the design, "
            "write and test the code, search for and check literature and fund records, and draft text. Every "
            "reference was checked against a bibliographic record, and four unverifiable references in the course "
            "example were dropped. Fund identities were checked against public records. No experimental result was "
            "produced by the assistant: the audited models' replies are the only source of results. The group "
            "reviewed and is responsible for all content. The full statement is in AI_use_statement.md.", ""]

    (ROOT / "report" / "appendices_generated.md").write_text("\n".join(out), encoding="utf-8")
    print("Wrote report/appendices_generated.md")


if __name__ == "__main__":
    main()
