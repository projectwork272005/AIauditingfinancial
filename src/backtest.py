"""Historical check of the recommended portfolios.

Step 1 (needs network access to the fund data source):
  python src/backtest.py fetch --source fuyao
      downloads a dividend-adjusted return index for every menu fund over the
      back-test window and stores it in data/nav/<code>.csv, with the source,
      retrieval time and raw file recorded in data/nav/_manifest.csv.
Step 2 (offline):
  python src/backtest.py evaluate
      computes fund-level metrics (outputs/tables/T_fund_history_metrics.csv)
      and portfolio-level metrics for every coded recommendation
      (outputs/portfolio_backtest.csv, keyed by call_id).

Method
------
* Window: the longest run of complete months, up to 60, that ends at
  2026-09-30 and for which every menu fund has data (start chosen
  automatically; the window used is written to every output row).
* Fund return index -> month-end values -> monthly returns.
* Portfolio = recommended weights, rebalanced monthly (on-menu funds only,
  weights renormalised exactly as in code_responses.py).
* Metrics: annualised return (CAGR), annualised volatility (monthly s.d. x
  sqrt(12)), maximum drawdown on the monthly index, and the worst rolling
  12-month return.
* Loss-tolerance check: the worst rolling 12-month return is compared with the
  maximum one-year loss stated in the investor's risk description
  (C1 0%, C2 5%, C3 15%, C4 25%, C5 40%).

These are historical, descriptive measures of how the recommended mix would
have behaved; they are not forecasts and say nothing about future returns.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from code_responses import normalize_holdings
from design import MAX_ONE_YEAR_LOSS_PCT

ROOT = Path(__file__).resolve().parents[1]
NAV_DIR = ROOT / "data" / "nav"
DEFAULT_START, DEFAULT_END = "auto", "2026-09-30"
MAX_MONTHS = 60


def auto_start(indices: dict[str, pd.Series], end: str) -> str:
    """First day of the first month for which every fund has a base value at the
    previous month-end, but no earlier than MAX_MONTHS months before `end`."""
    first_common = max(s.dropna().index.min() for s in indices.values())
    first_month_end = first_common + pd.offsets.MonthEnd(0)
    start_data = first_month_end + pd.Timedelta(days=1)
    start_cap = pd.Timestamp(end) - pd.DateOffset(months=MAX_MONTHS) + pd.Timedelta(days=1)
    return max(start_data, start_cap).strftime("%Y-%m-%d")


def monthly_returns(index_by_code: dict[str, pd.Series], start: str, end: str) -> pd.DataFrame:
    frame = {}
    for code, s in index_by_code.items():
        s = s.sort_index()
        # keep one extra month so the first month in the window has a base value
        s = s[(s.index >= pd.Timestamp(start) - pd.DateOffset(months=1)) & (s.index <= end)]
        frame[code] = s.resample("ME").last()
    levels = pd.DataFrame(frame)
    rets = levels.pct_change().iloc[1:]
    return rets[(rets.index >= start) & (rets.index <= end)]


def series_metrics(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 13:
        return {"n_months": len(r)}
    idx = (1 + r).cumprod()
    years = len(r) / 12
    roll12 = (1 + r).rolling(12).apply(np.prod, raw=True) - 1
    dd = idx / idx.cummax() - 1
    return {
        "n_months": len(r),
        "cagr_pct": 100 * (idx.iloc[-1] ** (1 / years) - 1),
        "vol_pct": 100 * r.std(ddof=1) * np.sqrt(12),
        "max_drawdown_pct": 100 * min(dd.min(), 0.0),
        "worst_12m_pct": 100 * roll12.min(),
        "best_12m_pct": 100 * roll12.max(),
        "share_negative_12m": float((roll12.dropna() < 0).mean()),
    }


def load_indices() -> dict[str, pd.Series]:
    out = {}
    for path in sorted(NAV_DIR.glob("[0-9]*.csv")):
        df = pd.read_csv(path, parse_dates=["date"])
        out[path.stem] = df.set_index("date")["return_index"]
    return out


def fetch(source_name: str, start: str, end: str):
    from fund_data import get_source
    src = get_source(source_name)
    menu = pd.read_csv(ROOT / "data" / "fund_menu.csv", dtype=str)
    NAV_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    base = pd.Timestamp(end) - pd.DateOffset(months=MAX_MONTHS) if start == "auto" else pd.Timestamp(start)
    fetch_start = (base - pd.DateOffset(months=2)).strftime("%Y-%m-%d")
    for code in menu["code"]:
        when = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            df = src.nav_history(code, fetch_start, end)
            df.to_csv(NAV_DIR / f"{code}.csv", index=False)
            manifest.append({"code": code, "source": src.name, "retrieved_utc": when, "rows": len(df),
                             "first_date": df["date"].min(), "last_date": df["date"].max(),
                             "raw_file": df.attrs.get("raw_file", "")})
            print(f"{code}: {len(df)} rows {df['date'].min():%Y-%m-%d} .. {df['date'].max():%Y-%m-%d}")
        except Exception as exc:
            manifest.append({"code": code, "source": src.name, "retrieved_utc": when, "error": str(exc)})
            print(f"{code}: FAILED {exc}")
    pd.DataFrame(manifest).to_csv(NAV_DIR / "_manifest.csv", index=False)


def evaluate(start: str, end: str):
    indices = load_indices()
    if start == "auto":
        start = auto_start(indices, end)
    monthly = monthly_returns(indices, start, end)
    menu = pd.read_csv(ROOT / "data" / "fund_menu.csv", dtype=str).set_index("code")
    missing = sorted(set(menu.index) - set(monthly.columns))
    if missing:
        raise SystemExit(f"No return history for {missing}; run 'fetch' first.")
    incomplete = [c for c in monthly.columns if monthly[c].isna().any()]
    if incomplete:
        raise SystemExit(f"Gaps in monthly history for {incomplete}; check the source data.")
    tables = ROOT / "outputs" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    fm = pd.DataFrame({c: series_metrics(monthly[c]) for c in monthly.columns}).T
    fm = menu[["name_cn", "category_en", "risk_rating"]].join(fm)
    fm.to_csv(tables / "T_fund_history_metrics.csv")

    results = pd.read_csv(ROOT / "outputs" / "experiment_results.csv")
    holdings = pd.read_csv(ROOT / "outputs" / "experiment_holdings.csv", dtype={"code": str})
    rows = []
    for call_id, hold in holdings.groupby("call_id"):
        w = normalize_holdings(hold)
        if w.empty:
            continue
        port = monthly[w["code"]].to_numpy() @ (w["w"].to_numpy() / 100)
        rows.append({"call_id": call_id, **series_metrics(pd.Series(port, index=monthly.index))})
    bt = pd.DataFrame(rows)
    bt = bt.merge(results[["call_id", "risk_class"]], on="call_id", how="left")
    bt["max_loss_tolerated_pct"] = bt["risk_class"].map(MAX_ONE_YEAR_LOSS_PCT)
    bt["loss_tolerance_breach"] = bt["worst_12m_pct"] < -bt["max_loss_tolerated_pct"]
    bt["drawdown_tolerance_breach"] = bt["max_drawdown_pct"] < -bt["max_loss_tolerated_pct"]
    bt["window"] = f"{start} to {end}"
    bt.drop(columns=["risk_class"]).to_csv(ROOT / "outputs" / "portfolio_backtest.csv", index=False)
    print(f"Back-tested {len(bt)} portfolios over {start} to {end} ({len(monthly)} months).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["fetch", "evaluate"])
    ap.add_argument("--source", default="fuyao")
    ap.add_argument("--start", default=DEFAULT_START)
    ap.add_argument("--end", default=DEFAULT_END)
    a = ap.parse_args()
    fetch(a.source, a.start, a.end) if a.step == "fetch" else evaluate(a.start, a.end)
