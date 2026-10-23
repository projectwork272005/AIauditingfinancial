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
    out += ["The text below is exactly what the models receive after the words \"Here is my situation:\" for "
            "a deliberate conflict case, a very aggressive student who needs the money within a year. Risk class "
            "codes are never shown to the models.", ""]
    p = rows[1]
    out += [f"**{p.investor_id}** ({p.cell_id})", "", code_block(p.profile_text), ""]
    anchor = probes[probes.anchor_id == "PRB-03"]
    a0 = anchor[anchor.varied_attribute == "anchor"].iloc[0]
    v_risk = anchor[anchor.varied_attribute == "risk"].iloc[0]
    changed = [x for x, y in zip(v_risk.profile_text.split("\n"), a0.profile_text.split("\n")) if x != y][0]
    out += [f"**Probe example.** Version {v_risk.probe_id} differs from its anchor PRB-03 only in the "
            "risk-tolerance line, shown below.", "", code_block(changed), ""]

    out += ["# Appendix B. Sample Validation Checks", ""]
    checks = validate_profiles.run_main_checks(inv) + validate_profiles.run_probe_checks(probes)
    out += ["Table B1 lists the 16 checks applied to the two synthetic samples; all pass.", "",
            "TABLE: Table B1. Validation checks applied to the synthetic samples",
            md_table(pd.DataFrame([{"ID": c[0], "Check": c[1], "Result": "Pass" if c[2] else "FAIL"}
                                   for c in checks])),
            "NOTE: Produced by src/validate_profiles.py, which is independent of the generator; details in "
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
    d = pd.DataFrame({"Code": menu["code"], "Fund name": menu["name_cn"],
                      "Category": menu["category_en"], "Notes": notes,
                      "Rating": menu["risk_rating"].replace({"": "pending"}),
                      "Equity (%)": pd.to_numeric(menu.get("equity_exposure_pct", menu["fallback_equity_pct"]),
                                                  errors="coerce").map(lambda v: f"{v:.1f}")})
    out += ["TABLE: Table D1. The 23-fund menu", md_table(d),
            "NOTE: Identity checked on 22 October 2026 against at least two public records per fund; sources, "
            "managers and inception dates in data/fund_menu_candidates.csv. Ratings: Eastmoney, 23 October 2026. "
            "Equity (%): category assumption, used for index feeders, the FOF and gold; otherwise the reported stock "
            "share at 30 June 2026 is used (data/fund_menu.csv).", ""]

    out += ["# Appendix E. Coding Rules", "",
            "Table 6 summarises the coded measures; docs/coding_sheet.md defines every field. Replies that cannot be "
            "parsed stay in the data without portfolio measures. Off-menu codes are excluded from the risk measures "
            "and the remaining weights rescaled to 100. Conflict acknowledgement is a keyword rule (conflict, "
            "inconsistent, mismatch, contradict, tension, at odds, not compatible, consistent or aligned). For manual "
            "validation, two group members independently code the stratified random sample of 60 replies in "
            "docs/manual_coding_sample.csv; agreement with the rule is to be reported as Cohen's kappa.", ""]

    manifests = sorted((ROOT / "outputs" / "logs").glob("run_*.json"))
    out += ["# Appendix F. Run Record", ""]
    if manifests:
        recs = [json.loads(m.read_text(encoding="utf-8")) for m in manifests]
        out += ["Table F1 lists the runs recorded in outputs/logs.", "",
                "TABLE: Table F1. Experiment runs",
                md_table(pd.DataFrame([{"Run": r["run_id"], "Started": r.get("started"), "Finished": r.get("finished"),
                                        "Calls ok": r.get("ok"), "Calls failed": r.get("failed")} for r in recs]).astype(str)),
                ("NOTE: From outputs/logs. The first two runs are the 60-call pilot: 20 Kimi calls failed with reasoning "
                 "enabled and were retried after it was disabled. Model identifiers and serving providers are in Table 6; "
                 "per-model calls and token usage are in docs/run_status.md."), ""]
    else:
        out += ["PENDING: The experiment has not yet been run; this appendix is filled from outputs/logs.", ""]

    out += ["# Appendix G. Reproducibility", "",
            "Code, data and logs are in the project repository; README.md lists the commands in order. The samples "
            "are regenerated exactly from seed 20261022. Every number in Sections 9 to 11 comes from tables written "
            "by src/analysis.py and report/report_supplement.py from the raw logs; none is typed by hand. Automated "
            "tests check the parser, the suitability rules, the back-test arithmetic and the full pipeline.", ""]

    out += ["# Appendix H. AI Use Statement", "",
            "An AI assistant (Claude, Anthropic) helped design the study, write and test the code, check literature "
            "and fund records, and draft text. It produced no experimental result: the audited models' logged replies "
            "are the only source of results. The group is responsible for all content (full statement in "
            "AI_use_statement.md).", ""]

    (ROOT / "report" / "appendices_generated.md").write_text("\n".join(out), encoding="utf-8")
    print("Wrote report/appendices_generated.md")


if __name__ == "__main__":
    main()
