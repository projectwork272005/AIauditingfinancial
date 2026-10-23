"""Risk-adjusted performance, benchmark comparison and costs of the recommended
portfolios (extends the historical check in backtest.py).

Added after the main analysis to cover the performance measures listed in the
course manual; it does not change any pre-specified metric or hypothesis.

Offline: reads data/nav/ (adjusted NAVs, already net of each fund's ongoing
management, custody and sales-service fees), the coded holdings, and the raw
fee schedules in data/fund_sources/raw/.

Measures per portfolio (same window and monthly rebalancing as backtest.py)
  CAGR, volatility, Sharpe ratio, maximum drawdown, Calmar ratio.
  Sharpe: mean monthly return in excess of the risk-free proxy x 12, divided by
  the s.d. of monthly excess returns x sqrt(12). Risk-free proxy: the monthly
  return of the money market fund 000198 (Tianhong Yu'e Bao) from the same data.
  Calmar: CAGR / |maximum drawdown| (undefined when there is no drawdown).

Benchmarks (all built from menu funds with the same data and window)
  60/40 stock-bond mix: 60% 110020 (CSI 300 index feeder) + 40% 000015 (pure
      bond fund), rebalanced monthly.
  Target-risk fund: 006580, a balanced target-risk pension fund of funds.
  Risk-matched model portfolio: a stylised robo-adviser style ladder that maps
      each risk class to a fixed mix of cash, bond, hybrid and index funds and
      never exceeds the class's product-rating ceiling (MODEL_PORTFOLIOS below).
      It is a researchers' construction, not a commercial robo-adviser's record.

Costs
  Ongoing fees are inside the NAV, so gross results are already net of them.
  Front-end purchase fees: the distributor's first-tier rate from Eastmoney
  (standard and discounted platform rate; cross-checked with the fuyao rate
  tables for the 19 funds that have them). Exit fees: fuyao redemption
  schedules at the holding period of the window; not retrieved for the four
  LOF funds (163406, 160119, 161725, 160416), whose exit fee is set to 0.
  Net A, buy and hold: purchase fee on the initial amount, no rebalancing,
      exit fee at the end of the window.
  Net B, monthly rebalancing: purchase fee on the initial amount and on every
      rebalancing purchase; redemption fees on rebalancing sales are not
      charged (they depend on the age of each lot), so B is a lower bound.

Writes
  outputs/portfolio_performance.csv              per call_id
  outputs/tables/T26_benchmark_performance.csv   benchmarks and model portfolios
  outputs/tables/T27_performance_by_risk_class.csv
  outputs/tables/T28_ai_vs_benchmarks.csv
  outputs/tables/T29_performance_by_model.csv
  outputs/tables/T30_costs_by_risk_class.csv
  outputs/tables/T33_performance_summary.csv     compact table for the report
  outputs/figures/F09_cumulative_growth_vs_benchmarks.png
  outputs/figures/F10_risk_return_vs_benchmarks.png

Run: python src/performance.py
"""

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from backtest import DEFAULT_END, auto_start, load_indices, monthly_returns  # noqa: E402
from code_responses import normalize_holdings  # noqa: E402
from design import MAX_ONE_YEAR_LOSS_PCT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "fund_sources" / "raw"
TABLES = ROOT / "outputs" / "tables"
RF_CODE = "000198"

BENCHMARKS = {
    "60/40 stock-bond mix": {"110020": 60, "000015": 40},
    "Target-risk fund (006580)": {"006580": 100},
}
MODEL_PORTFOLIOS = {
    "C1": {"000198": 100},
    "C2": {"000198": 40, "000015": 60},
    "C3": {"000198": 20, "000015": 50, "001316": 30},
    "C4": {"000015": 50, "110020": 50},
    "C5": {"000015": 25, "110020": 75},
}
RISK_CLASSES = list(MODEL_PORTFOLIOS)


# ------------------------------------------------------------------ metrics --
def perf_metrics(r: pd.Series, rf: pd.Series) -> dict:
    idx = (1 + r).cumprod()
    years = len(r) / 12
    cagr = idx.iloc[-1] ** (1 / years) - 1
    dd = float(min((idx / idx.cummax() - 1).min(), 0.0))
    ex = r - rf
    sd = ex.std(ddof=1)
    sharpe = ex.mean() * 12 / (sd * np.sqrt(12)) if sd > 1e-9 else np.nan
    return {
        "cagr_pct": 100 * cagr,
        "vol_pct": 100 * r.std(ddof=1) * np.sqrt(12),
        "sharpe": sharpe,
        "max_drawdown_pct": 100 * dd,
        "calmar": cagr / abs(dd) if dd < -1e-6 else np.nan,
        "total_return_pct": 100 * (idx.iloc[-1] - 1),
        "worst_12m_pct": 100 * float(((1 + r).rolling(12).apply(np.prod, raw=True) - 1).min()),
    }


# --------------------------------------------------------------------- fees --
def _latest(pattern: str) -> Path | None:
    files = sorted(RAW.glob(pattern))
    return files[-1] if files else None


def _json(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.find("{"):])


def _pct(s) -> float:
    if s is None or "%" not in str(s):
        return np.nan
    return float(str(s).replace("%", "")) / 100


def _days_range(cond: str | None) -> tuple[float, float]:
    if not cond:
        return 0, np.inf
    m = re.fullmatch(r"(\d+)天以下", cond)
    if m:
        return 0, float(m[1])
    m = re.fullmatch(r"(\d+)天\(包含\)-(\d+)天", cond)
    if m:
        return float(m[1]), float(m[2])
    m = re.fullmatch(r"(\d+)天以上\(包含\)", cond)
    if m:
        return float(m[1]), np.inf
    raise ValueError(f"unrecognised redemption condition {cond!r}")


def fee_table(codes, holding_days: float) -> pd.DataFrame:
    rows = []
    for code in codes:
        row = {"code": code, "purchase_std": np.nan, "purchase_disc": np.nan, "exit_fee": np.nan,
               "fee_source": ""}
        em = _latest(f"eastmoney_{code}_basic_*")
        if em:
            x = _json(em).get("Datas", {})
            row["purchase_std"], row["purchase_disc"] = _pct(x.get("SOURCERATE")), _pct(x.get("RATE"))
            row["fee_source"] = "eastmoney"
        fy = _latest(f"fuyao_{code}_profile_*")
        rates = []
        if fy:
            d = _json(fy)
            if d.get("code") == 0:
                rates = d["data"]["item"][0].get("rate_info") or []
        purchase = [r for r in rates if r["rate_type"] == "purchase"]
        if purchase:
            first = purchase[0]
            std, disc = _pct(first.get("standard_rate")), _pct(first.get("discounted_rate"))
            if np.isnan(row["purchase_std"]):
                row["purchase_std"], row["purchase_disc"] = std, disc if not np.isnan(disc) else std
                row["fee_source"] = "fuyao"
            row["purchase_check"] = (np.isclose(row["purchase_std"], std) and
                                     (np.isnan(disc) or np.isclose(row["purchase_disc"], disc)))
        redemption = [r for r in rates if r["rate_type"] == "redemption"]
        for r in redemption:
            lo, hi = _days_range(r.get("condition"))
            if lo <= holding_days < hi:
                row["exit_fee"] = _pct(r.get("standard_rate"))
        row["exit_fee_known"] = not np.isnan(row["exit_fee"])
        if not row["exit_fee_known"]:
            row["exit_fee"] = 0.0
        rows.append(row)
    out = pd.DataFrame(rows).set_index("code")
    if out[["purchase_std", "purchase_disc"]].isna().any().any():
        raise SystemExit(f"Missing purchase fee for {out[out['purchase_disc'].isna()].index.tolist()}")
    return out


def net_buy_and_hold(w: pd.Series, monthly: pd.DataFrame, fees: pd.DataFrame, rate_col: str) -> float:
    """Annualised return after the purchase fee (charged on the gross amount,
    amount / (1 + rate) invested) and the exit fee, without rebalancing."""
    growth = (1 + monthly[w.index]).prod()
    invested = w / (1 + fees.loc[w.index, rate_col])
    end = (invested * growth * (1 - fees.loc[w.index, "exit_fee"])).sum()
    return 100 * (end ** (12 / len(monthly)) - 1)


def gross_buy_and_hold(w: pd.Series, monthly: pd.DataFrame) -> float:
    end = (w * (1 + monthly[w.index]).prod()).sum()
    return 100 * (end ** (12 / len(monthly)) - 1)


def net_rebalanced(w: pd.Series, monthly: pd.DataFrame, fees: pd.DataFrame) -> tuple[pd.Series, float]:
    """Monthly rebalancing with the discounted purchase fee on the initial amount and
    on every rebalancing purchase. Returns the net monthly return series and the
    average monthly one-way turnover."""
    rate = fees.loc[w.index, "purchase_disc"].to_numpy()
    target = w.to_numpy()
    v = target / (1 + rate)                     # initial purchase
    total_prev = 1.0
    rets, turns = [], []
    for _, r in monthly[w.index].iterrows():
        v = v * (1 + r.to_numpy())
        total = v.sum()
        buys = np.clip(target * total - v, 0, None)
        cost = (buys * rate / (1 + rate)).sum()
        turns.append(buys.sum() / total)
        total_net = total - cost
        v = target * total_net
        rets.append(total_net / total_prev - 1)
        total_prev = total_net
    return pd.Series(rets, index=monthly.index), float(np.mean(turns[1:])) if len(turns) > 1 else 0.0


# --------------------------------------------------------------------- main --
def weights_of(spec: dict) -> pd.Series:
    w = pd.Series(spec, dtype=float)
    return w / w.sum()


def main():
    indices = load_indices()
    start = auto_start(indices, DEFAULT_END)
    monthly = monthly_returns(indices, start, DEFAULT_END)
    window = f"{start} to {DEFAULT_END}"
    rf = monthly[RF_CODE]
    holding_days = (pd.Timestamp(DEFAULT_END) - pd.Timestamp(start)).days
    fees = fee_table(monthly.columns, holding_days)
    fees.to_csv(TABLES / "T_fund_fees.csv")
    # upper bound for the four funds without a retrieved redemption schedule:
    # the highest exit fee among the funds whose schedule is known
    fees_hi = fees.copy()
    fees_hi.loc[~fees_hi["exit_fee_known"], "exit_fee"] = fees.loc[fees["exit_fee_known"], "exit_fee"].max()

    def evaluate(w: pd.Series) -> dict:
        r = pd.Series(monthly[w.index].to_numpy() @ w.to_numpy(), index=monthly.index)
        out = perf_metrics(r, rf)
        out["gross_bh_cagr_pct"] = gross_buy_and_hold(w, monthly)
        out["net_bh_cagr_pct"] = net_buy_and_hold(w, monthly, fees, "purchase_disc")
        out["net_bh_std_fee_cagr_pct"] = net_buy_and_hold(w, monthly, fees, "purchase_std")
        out["net_bh_std_fee_exit_hi_cagr_pct"] = net_buy_and_hold(w, monthly, fees_hi, "purchase_std")
        rn, turnover = net_rebalanced(w, monthly, fees)
        net = perf_metrics(rn, rf)
        out["net_rebal_cagr_pct"], out["net_rebal_sharpe"] = net["cagr_pct"], net["sharpe"]
        out["monthly_turnover_pct"] = 100 * turnover
        out["purchase_fee_disc_pct"] = 100 * float((w * fees.loc[w.index, "purchase_disc"]).sum())
        out["purchase_fee_std_pct"] = 100 * float((w * fees.loc[w.index, "purchase_std"]).sum())
        out["weight_unknown_exit_fee_pct"] = 100 * float(w[~fees.loc[w.index, "exit_fee_known"]].sum())
        return out, r

    # benchmarks and model portfolios
    bench_rows, bench_series = [], {}
    for name, spec in BENCHMARKS.items():
        m, r = evaluate(weights_of(spec))
        bench_rows.append({"benchmark": name, "risk_class": "all", **m})
        bench_series[name] = r
    for rc, spec in MODEL_PORTFOLIOS.items():
        m, r = evaluate(weights_of(spec))
        name = f"Risk-matched model portfolio {rc}"
        bench_rows.append({"benchmark": name, "risk_class": rc, **m})
        bench_series[name] = r
    bench = pd.DataFrame(bench_rows)
    bench["composition"] = [", ".join(f"{k} {v}%" for k, v in spec.items())
                            for spec in list(BENCHMARKS.values()) + list(MODEL_PORTFOLIOS.values())]
    bench["window"] = window
    bench.round(4).to_csv(TABLES / "T26_benchmark_performance.csv", index=False)

    # AI portfolios
    results = pd.read_csv(ROOT / "outputs" / "experiment_results.csv", dtype={"unit_id": str})
    holdings = pd.read_csv(ROOT / "outputs" / "experiment_holdings.csv", dtype={"code": str})
    rows, series = [], {}
    for call_id, hold in holdings.groupby("call_id"):
        h = normalize_holdings(hold)
        if h.empty:
            continue
        w = pd.Series(h["w"].to_numpy() / 100, index=h["code"]).groupby(level=0).sum()
        m, r = evaluate(w)
        rows.append({"call_id": call_id, **m})
        series[call_id] = r
    perf = pd.DataFrame(rows)
    perf["window"] = window
    perf.round(4).to_csv(ROOT / "outputs" / "portfolio_performance.csv", index=False)

    main_s = results[(results["sample"] == "main")][["call_id", "model_key", "condition", "risk_class"]]
    x = main_s.merge(perf, on="call_id", how="inner")
    b60 = bench.set_index("benchmark").loc["60/40 stock-bond mix"]
    btr = bench.set_index("benchmark").loc["Target-risk fund (006580)"]
    bmp = bench[bench["risk_class"] != "all"].set_index("risk_class")
    x["mp_sharpe"] = x["risk_class"].map(bmp["sharpe"])
    x["mp_cagr"] = x["risk_class"].map(bmp["cagr_pct"])
    x["mp_mdd"] = x["risk_class"].map(bmp["max_drawdown_pct"])

    metrics = ["cagr_pct", "vol_pct", "sharpe", "max_drawdown_pct", "calmar"]
    t27 = (x.groupby(["condition", "risk_class"])
           .agg(n=("call_id", "size"), **{f"median_{k}": (k, "median") for k in metrics}).reset_index())
    t27.round(3).to_csv(TABLES / "T27_performance_by_risk_class.csv", index=False)

    def beats(g, col, ref):
        ok = g[col].notna() & pd.Series(ref, index=g.index).notna()
        return 100 * (g.loc[ok, col] > pd.Series(ref, index=g.index)[ok]).mean() if ok.any() else np.nan

    t28 = []
    for (cond, rc), g in x.groupby(["condition", "risk_class"]):
        t28.append({
            "condition": cond, "risk_class": rc, "n": len(g),
            "sharpe_above_6040_pct": beats(g, "sharpe", b60["sharpe"]),
            "sharpe_above_target_risk_pct": beats(g, "sharpe", btr["sharpe"]),
            "sharpe_above_model_pct": beats(g, "sharpe", g["mp_sharpe"]),
            "cagr_above_model_pct": 100 * (g["cagr_pct"] > g["mp_cagr"]).mean(),
            "median_cagr_minus_model_pp": (g["cagr_pct"] - g["mp_cagr"]).median(),
            "median_mdd_minus_model_pp": (g["max_drawdown_pct"] - g["mp_mdd"]).median(),
        })
    pd.DataFrame(t28).round(2).to_csv(TABLES / "T28_ai_vs_benchmarks.csv", index=False)

    t29 = (x.groupby(["model_key", "condition"])
           .agg(n=("call_id", "size"), median_cagr_pct=("cagr_pct", "median"),
                median_vol_pct=("vol_pct", "median"), median_sharpe=("sharpe", "median"),
                median_max_drawdown_pct=("max_drawdown_pct", "median"), median_calmar=("calmar", "median"))
           .reset_index())
    t29["sharpe_above_model_pct"] = [beats(g, "sharpe", g["mp_sharpe"])
                                     for _, g in x.groupby(["model_key", "condition"])]
    t29.round(3).to_csv(TABLES / "T29_performance_by_model.csv", index=False)

    x["cost_drag_bh_pp"] = x["gross_bh_cagr_pct"] - x["net_bh_cagr_pct"]
    x["cost_drag_bh_std_pp"] = x["gross_bh_cagr_pct"] - x["net_bh_std_fee_cagr_pct"]
    x["cost_drag_bh_hi_pp"] = x["gross_bh_cagr_pct"] - x["net_bh_std_fee_exit_hi_cagr_pct"]
    x["cost_drag_rebal_pp"] = x["cagr_pct"] - x["net_rebal_cagr_pct"]
    t30 = (x.groupby(["condition", "risk_class"])
           .agg(n=("call_id", "size"),
                median_purchase_fee_disc_pct=("purchase_fee_disc_pct", "median"),
                median_purchase_fee_std_pct=("purchase_fee_std_pct", "median"),
                median_gross_bh_cagr_pct=("gross_bh_cagr_pct", "median"),
                median_net_bh_cagr_pct=("net_bh_cagr_pct", "median"),
                median_cost_drag_bh_pp=("cost_drag_bh_pp", "median"),
                median_cost_drag_bh_std_fee_pp=("cost_drag_bh_std_pp", "median"),
                max_cost_drag_bh_std_fee_exit_hi_pp=("cost_drag_bh_hi_pp", "max"),
                median_gross_rebal_cagr_pct=("cagr_pct", "median"),
                median_monthly_turnover_pct=("monthly_turnover_pct", "median"),
                median_cost_drag_rebal_pp=("cost_drag_rebal_pp", "median"),
                share_with_unknown_exit_fee_pct=("weight_unknown_exit_fee_pct", lambda s: 100 * (s > 0).mean()))
           .reset_index())
    t30.round(3).to_csv(TABLES / "T30_costs_by_risk_class.csv", index=False)

    # compact summary for the report: AI portfolios pooled over models and conditions
    x["loss_breach"] = x["worst_12m_pct"] < -x["risk_class"].map(MAX_ONE_YEAR_LOSS_PCT)
    t33 = []
    for rc, g in x.groupby("risk_class"):
        t33.append({"portfolio": f"AI portfolios {rc}", "n": len(g),
                    **{k: g[k].median() for k in metrics + ["worst_12m_pct"]},
                    "loss_breach_pct": 100 * g["loss_breach"].mean(),
                    "sharpe_above_6040_pct": beats(g, "sharpe", b60["sharpe"]),
                    "sharpe_above_target_risk_pct": beats(g, "sharpe", btr["sharpe"]),
                    "sharpe_above_model_pct": beats(g, "sharpe", g["mp_sharpe"]),
                    "median_return_lost_std_fee_pp": g["cost_drag_bh_std_pp"].median(),
                    "max_return_lost_pp": g["cost_drag_bh_hi_pp"].max()})
    for _, b in bench.iterrows():
        t33.append({"portfolio": b["benchmark"], "n": 1, **{k: b[k] for k in metrics + ["worst_12m_pct"]}})
    pd.DataFrame(t33).round(3).to_csv(TABLES / "T33_performance_summary.csv", index=False)

    figures(x, series, bench_series, bench, window)
    print(f"Performance: {len(perf)} portfolios, window {window}; tables T26-T30, figures F09-F10")


# ------------------------------------------------------------------ figures --
def figures(x, series, bench_series, bench, window):
    from figures import COND_LABEL, INK, MODEL_COLORS, MUTED  # same style as the other figures
    out = ROOT / "outputs" / "figures"
    ai_color = MODEL_COLORS[0]
    bench_style = {"60/40 stock-bond mix": {"color": INK, "ls": ":"},
                   "Target-risk fund (006580)": {"color": MUTED, "ls": "-."},
                   "model": {"color": "#8C8C8C", "ls": "-"}}

    # F09 cumulative growth by risk class
    fig, axes = plt.subplots(1, 5, figsize=(11, 3.4), sharey=True)
    for ax, rc in zip(axes, RISK_CLASSES):
        for cond, alpha, ls in (("BASE", 0.5, "--"), ("SUIT", 1.0, "-")):
            ids = x[(x["risk_class"] == rc) & (x["condition"] == cond)]["call_id"]
            mean_r = pd.concat([series[i] for i in ids], axis=1).mean(axis=1)
            ax.plot((1 + mean_r).cumprod() * 100, color=ai_color, alpha=alpha, ls=ls,
                    label=f"Average AI portfolio - {COND_LABEL[cond]}")
        for name in BENCHMARKS:
            st = bench_style[name]
            ax.plot((1 + bench_series[name]).cumprod() * 100, color=st["color"], ls=st["ls"], lw=1.4, label=name)
        st = bench_style["model"]
        ax.plot((1 + bench_series[f"Risk-matched model portfolio {rc}"]).cumprod() * 100, color=st["color"],
                ls=st["ls"], lw=1.4, label="Risk-matched model portfolio")
        ax.set_title(rc, fontsize=9, color=INK)
        ax.tick_params(axis="x", labelrotation=45, labelsize=7)
        ax.axhline(100, color="#BDBDBD", lw=0.8)
    axes[0].set_ylabel("Value of 100 invested (gross of purchase fees)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=3, fontsize=7,
               frameon=False)
    fig.savefig(out / "F09_cumulative_growth_vs_benchmarks.png")
    plt.close(fig)

    # F10 risk-return scatter by risk class
    fig, axes = plt.subplots(1, 5, figsize=(11, 3.4), sharey=True, sharex=True)
    for ax, rc in zip(axes, RISK_CLASSES):
        for cond, alpha in (("BASE", 0.25), ("SUIT", 0.6)):
            g = x[(x["risk_class"] == rc) & (x["condition"] == cond)]
            ax.scatter(g["vol_pct"], g["cagr_pct"], s=10, color=ai_color, alpha=alpha, lw=0,
                       label=f"AI portfolio - {COND_LABEL[cond]}")
        b = bench.set_index("benchmark")
        for name, marker in (("60/40 stock-bond mix", "s"), ("Target-risk fund (006580)", "D"),
                             (f"Risk-matched model portfolio {rc}", "^")):
            ax.scatter(b.loc[name, "vol_pct"], b.loc[name, "cagr_pct"], s=40, marker=marker, color=INK,
                       edgecolor="white", lw=1, zorder=3,
                       label=name if not name.startswith("Risk") else "Risk-matched model portfolio")
        ax.set_title(rc, fontsize=9, color=INK)
        ax.set_xlabel("Volatility (% p.a.)", fontsize=8)
    axes[0].set_ylabel("Annualised return (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=3, fontsize=7,
               frameon=False)
    fig.savefig(out / "F10_risk_return_vs_benchmarks.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
