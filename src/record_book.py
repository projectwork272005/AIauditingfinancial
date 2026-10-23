"""Excel record book: every input, prompt, conversation and coded result of the
experiment in one workbook (outputs/record_book.xlsx), following the course
demonstration workbook (profiles -> candidate list -> AI recommendations).

Everything is copied from the project files; nothing is typed by hand.
Run after the analysis scripts:  python src/record_book.py
"""

import json
from pathlib import Path

import pandas as pd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "record_book.xlsx"
EXCEL_CELL_MAX = 32767


def clean(v):
    if isinstance(v, str):
        v = ILLEGAL_CHARACTERS_RE.sub("", v)
        if len(v) > EXCEL_CELL_MAX:
            raise SystemExit(f"Cell longer than Excel allows ({len(v)} characters)")
    return v


def conversations() -> pd.DataFrame:
    rows = []
    for path in sorted((ROOT / "outputs" / "raw").glob("calls_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            usage = r.get("usage") or {}
            rows.append({
                "call_id": r["call_id"], "model_key": r["model_key"], "condition": r["condition"],
                "sample": r["sample"], "unit_id": r["unit_id"], "replicate": r["replicate"], "run_id": r["run_id"],
                "started_utc": r["started_utc"], "finished_utc": r["finished_utc"], "route": r.get("provider_route"),
                "model_requested": r.get("model_requested"), "model_returned": r.get("model_returned"),
                "provider": r.get("provider"), "system_prompt_sha256": r.get("system_prompt_sha256"),
                "user_prompt": r.get("user_prompt"), "reply": r.get("content"), "ok": r.get("ok"),
                "error": r.get("error"), "finish_reason": r.get("finish_reason"),
                "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                "cost_usd": usage.get("cost"), "attempts": r.get("attempts"), "latency_s": r.get("latency_s"),
            })
    return pd.DataFrame(rows).sort_values(["started_utc", "call_id"])


def prompts() -> pd.DataFrame:
    rows = []
    for path in sorted((ROOT / "outputs" / "raw" / "prompts").glob("*.txt")):
        rows.append({"file": path.name, "text": path.read_text(encoding="utf-8")})
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from prompts import USER_TEMPLATE
    rows.append({"file": "user message template (src/prompts.py)", "text": USER_TEMPLATE})
    return pd.DataFrame(rows)


def readme(sheets: dict) -> pd.DataFrame:
    notes = {
        "1-Investor profiles": "200 synthetic investors, 5 horizons x 5 risk classes x 8 age bands (data/investor_profiles.csv)",
        "1b-Probe profiles": "160 single-attribute probe versions of 10 anchors (audit pairs; data/probe_profiles.csv)",
        "2-Fund menu": "23 verified funds with risk rating and equity basis (data/fund_menu.csv)",
        "2b-Fund verification": "Identity and rating checks per fund (data/fund_menu_verification.csv)",
        "3-Prompts": "System prompts (BASE, SUIT) with hashes and the user message template",
        "4-AI conversations": "Every logged call: full user prompt and full model reply, model, provider, tokens, time",
        "5-Coded results": "One row per reply: parse status, portfolio measures, suitability flags (outputs/experiment_results.csv)",
        "6-Holdings": "One row per recommended fund (outputs/experiment_holdings.csv)",
        "7-Backtest": "Back-test metrics per portfolio, Nov 2021 - Sep 2026 (outputs/portfolio_backtest.csv)",
        "8-Performance": "Sharpe, Calmar, net-of-fee returns per portfolio (outputs/portfolio_performance.csv)",
        "9-Benchmarks": "60/40 mix, target-risk fund and risk-matched model portfolios (T26)",
        "10-Fund history and fees": "Fund-level return history metrics and fee rates (T_fund_history_metrics, T_fund_fees)",
        "11-Double coding": "Status of the two-coder coding of the conflict item (docs/manual_coding)",
    }
    return pd.DataFrame([{"sheet": k, "rows": len(v), "content": notes.get(k, "")} for k, v in sheets.items()])


def double_coding() -> pd.DataFrame:
    cons = ROOT / "outputs" / "manual_coding_consensus.csv"
    if cons.exists():
        return pd.read_csv(cons)
    key = pd.read_csv(ROOT / "docs" / "manual_coding" / "key.csv")
    key["coder_A"] = ""
    key["coder_B"] = ""
    key["consensus"] = ""
    key["status"] = "not yet coded: coders work in docs/manual_coding/coder_A.csv and coder_B.csv"
    return key


def main():
    t = ROOT / "outputs" / "tables"
    hist = pd.read_csv(t / "T_fund_history_metrics.csv", dtype=str).rename(columns={"Unnamed: 0": "code"})
    fees = pd.read_csv(t / "T_fund_fees.csv", dtype={"code": str})
    sheets = {
        "1-Investor profiles": pd.read_csv(ROOT / "data" / "investor_profiles.csv"),
        "1b-Probe profiles": pd.read_csv(ROOT / "data" / "probe_profiles.csv"),
        "2-Fund menu": pd.read_csv(ROOT / "data" / "fund_menu.csv", dtype=str),
        "2b-Fund verification": pd.read_csv(ROOT / "data" / "fund_menu_verification.csv", dtype=str),
        "3-Prompts": prompts(),
        "4-AI conversations": conversations(),
        "5-Coded results": pd.read_csv(ROOT / "outputs" / "experiment_results.csv"),
        "6-Holdings": pd.read_csv(ROOT / "outputs" / "experiment_holdings.csv", dtype={"code": str, "raw_code": str}),
        "7-Backtest": pd.read_csv(ROOT / "outputs" / "portfolio_backtest.csv"),
        "8-Performance": pd.read_csv(ROOT / "outputs" / "portfolio_performance.csv"),
        "9-Benchmarks": pd.read_csv(t / "T26_benchmark_performance.csv"),
        "10-Fund history and fees": hist.merge(fees, on="code", how="left"),
        "11-Double coding": double_coding(),
    }
    sheets = {"0-README": readme(sheets), **sheets}
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df = df.map(clean) if hasattr(df, "map") else df.applymap(clean)
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF")
                c.fill = PatternFill("solid", fgColor="365B7E")
            for j, col in enumerate(df.columns, 1):
                long_text = df[col].astype(str).str.len().max() > 200 if len(df) else False
                ws.column_dimensions[get_column_letter(j)].width = 70 if long_text else min(
                    max(12, len(str(col)) + 2), 30)
                if long_text:
                    for cell in ws[get_column_letter(j)][1:]:
                        cell.alignment = Alignment(wrap_text=True, vertical="top")
    print(f"Wrote {OUT} ({', '.join(f'{k}: {len(v)}' for k, v in sheets.items())})")


if __name__ == "__main__":
    main()
