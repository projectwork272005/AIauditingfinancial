"""Statistical analysis of the coded recommendations.

Reads only outputs/experiment_results.csv (plus outputs/raw logs for call
counts and outputs/portfolio_backtest.csv when the historical check has been
run). Writes numbered tables to outputs/tables/ and a plain-text digest of
every reported statistic to outputs/tables/results_digest.md, which is the
single place the report takes numbers from.

Run: python src/analysis.py
"""

import json
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pingouin as pg
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.contingency_tables import cochrans_q, mcnemar
from statsmodels.stats.multitest import multipletests

# A probe series with identical equity at every level has no defined rank correlation; it is
# recorded as NaN and skipped by nanmean, so the warning carries no information.
warnings.filterwarnings("ignore", category=stats.ConstantInputWarning)

ROOT = Path(__file__).resolve().parents[1]
H_ORD = {f"H{i}": i for i in range(1, 6)}
A_ORD = {f"A{i}": i for i in range(1, 9)}


# ---------------------------------------------------------------- loading --

def load(out_root: Path = ROOT / "outputs") -> dict:
    path = out_root / "experiment_results.csv"
    if not path.exists():
        raise SystemExit("outputs/experiment_results.csv not found: run the experiment and code_responses.py first.")
    res = pd.read_csv(path, dtype={"unit_id": str})
    bt_path = out_root / "portfolio_backtest.csv"
    if bt_path.exists():
        res = res.merge(pd.read_csv(bt_path), on="call_id", how="left")
    res["horizon_level"] = res["horizon_band"].map(H_ORD)
    res["age_level"] = res["age_band"].map(A_ORD)
    res = res[res["sample"] != "pilot"]
    return {
        "all": res,
        "main": res[res["sample"] == "main"].copy(),
        "cons": res[res["sample"].isin(["main", "consistency"])].copy(),
        "probe": res[res["sample"] == "probe"].copy(),
    }


def cells(df: pd.DataFrame):
    for (m, c), g in df.groupby(["model_key", "condition"], sort=True):
        yield m, c, g


# --------------------------------------------------------------- helpers --

def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    if ok.any():
        out[ok] = multipletests(p[ok], method="holm")[1]
    return out


def partial_eta_sq(aov: pd.DataFrame) -> pd.Series:
    ss_res = aov.loc["Residual", "sum_sq"]
    return aov["sum_sq"].drop("Residual") / (aov["sum_sq"].drop("Residual") + ss_res)


def rank_biserial_paired(diff: np.ndarray) -> float:
    d = diff[diff != 0]
    if len(d) == 0:
        return 0.0
    ranks = stats.rankdata(np.abs(d))
    return float((ranks[d > 0].sum() - ranks[d < 0].sum()) / ranks.sum())


def mean_ci(x, conf=0.95):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return np.nan, np.nan, np.nan
    m, se = x.mean(), stats.sem(x)
    h = se * stats.t.ppf((1 + conf) / 2, len(x) - 1)
    return m, m - h, m + h


# ---------------------------------------------------------------- tables --

def t_feasibility(d, raw_dir: Path) -> pd.DataFrame:
    attempts = []
    for path in sorted(raw_dir.glob("calls_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                attempts.append({"call_id": r["call_id"], "ok": r.get("ok", False), "sample": r["sample"],
                                 "model_key": r["model_key"], "condition": r["condition"]})
    att = pd.DataFrame(attempts)
    att = att[att["sample"] == "main"] if len(att) else att
    m = d["main"]
    rows = []
    for (mk, c), g in m.groupby(["model_key", "condition"]):
        a = att[(att["model_key"] == mk) & (att["condition"] == c)] if len(att) else att
        n_units = a["call_id"].nunique() if len(a) else np.nan
        rows.append({
            "model": mk, "condition": c,
            "calls_planned": 200, "calls_with_success": len(g),
            "never_succeeded": (n_units - len(g)) if len(a) else np.nan,
            "parse_ok_pct": 100 * g["parse_status"].isin(["ok", "fenced"]).mean(),
            "parse_failed_pct": 100 * (g["parse_status"] == "failed").mean(),
            "codable_pct": 100 * g["portfolio_codable"].mean(),
            "weight_sum_ok_pct": 100 * g["weight_sum_ok"].mean(),
            "any_off_menu_pct": 100 * (g["off_menu_count"] > 0).mean(),
            "fund_count_ok_pct": 100 * g["fund_count_ok"].mean(),
            "mean_n_funds": g["n_funds"].mean(),
            "dca_pct": 100 * g["dca_recommended"].astype(float).mean(),
            "rebalancing_rule_pct": 100 * g["has_rebalancing_rule"].astype(float).mean(),
            "mean_risk_warnings": g["n_risk_warnings"].mean(),
            "prompt_tokens_total": g["prompt_tokens"].sum(),
            "completion_tokens_total": g["completion_tokens"].sum(),
        })
    return pd.DataFrame(rows)


def t_means_by_factor(m: pd.DataFrame, factor: str, outcome: str = "equity_pct") -> pd.DataFrame:
    g = m.groupby(["model_key", "condition", factor])[outcome]
    t = g.agg(["count", "mean", "std", "median"]).reset_index()
    return t.rename(columns={"count": "n"})


def t_spearman(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mk, c, g in cells(m):
        for outcome in ("equity_pct", "weighted_risk"):
            for factor in ("risk_level", "horizon_level", "age_level"):
                x = g[[factor, outcome]].dropna()
                rho, p = stats.spearmanr(x[factor], x[outcome])
                rows.append({"model": mk, "condition": c, "outcome": outcome, "factor": factor,
                             "n": len(x), "rho": rho, "p": p})
    t = pd.DataFrame(rows)
    t["p_holm"] = holm(t["p"])
    return t


def t_anova(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mk, c, g in cells(m):
        g = g.dropna(subset=["equity_pct"])
        fit = smf.ols("equity_pct ~ C(risk_class) + C(horizon_band) + C(age_band)", data=g).fit()
        aov = anova_lm(fit, typ=2)
        pe = partial_eta_sq(aov)
        total = aov["sum_sq"].sum()
        for term in pe.index:
            rows.append({"model": mk, "condition": c, "factor": term.replace("C(", "").replace(")", ""),
                         "df": aov.loc[term, "df"], "F": aov.loc[term, "F"], "p": aov.loc[term, "PR(>F)"],
                         "partial_eta_sq": pe[term], "eta_sq": aov.loc[term, "sum_sq"] / total,
                         "n": int(fit.nobs), "r_squared": fit.rsquared})
    t = pd.DataFrame(rows)
    t["p_holm"] = holm(t["p"])
    return t


def t_pooled_regression(m: pd.DataFrame, covariates: bool = False) -> pd.DataFrame:
    g = m.dropna(subset=["equity_pct"]).copy()
    for col in ("risk_level", "horizon_level", "age_level"):
        g[col + "_c"] = g[col] - g[col].mean()
    formula = ("equity_pct ~ (risk_level_c + horizon_level_c + age_level_c) * C(condition, Treatment('BASE'))"
               " + C(model_key)")
    if covariates:
        g["log_amount"] = np.log(g["investable_amount_cny"])
        formula += " + experience_years + log_amount + C(income_stability)"
    fit = smf.ols(formula, data=g).fit(cov_type="cluster", cov_kwds={"groups": g["unit_id"]})
    ci = fit.conf_int()
    return pd.DataFrame({"term": fit.params.index, "coef": fit.params.values, "se_cluster": fit.bse.values,
                         "ci_low": ci[0].values, "ci_high": ci[1].values, "p": fit.pvalues.values,
                         "n": int(fit.nobs), "r_squared": fit.rsquared})


def t_suitability(m: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    cols = {"rating_breach": "rating_breach_pct", "equity_over_cap": "equity_over_cap_pct",
            "holding_period_breach": "holding_period_breach_pct"}
    if "loss_tolerance_breach" in m:
        cols["loss_tolerance_breach"] = "loss_tolerance_breach_pct"
    g = m.dropna(subset=["rating_breach"]).groupby(by)
    t = g[list(cols)].apply(lambda x: 100 * x.astype(float).mean()).rename(columns=cols)
    t["n"] = g.size()
    t["mean_breach_weight"] = g["rating_breach_weight"].mean()
    t["mean_excess_equity"] = g["excess_equity"].mean()
    return t.reset_index()


def paired(m: pd.DataFrame, value: str) -> pd.DataFrame:
    w = m.pivot_table(index=["model_key", "unit_id"], columns="condition", values=value, aggfunc="first")
    return w.dropna()


def t_condition_effects(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mk in sorted(m["model_key"].unique()):
        mm = m[m["model_key"] == mk]
        for value in ("equity_pct", "weighted_risk"):
            w = paired(mm, value)
            if len(w) < 5:
                continue
            diff = (w["SUIT"] - w["BASE"]).to_numpy()
            stat, p = stats.wilcoxon(w["SUIT"], w["BASE"], zero_method="wilcox")
            mean, lo, hi = mean_ci(diff)
            rows.append({"model": mk, "outcome": value, "test": "Wilcoxon signed-rank", "n_pairs": len(w),
                         "mean_BASE": w["BASE"].mean(), "mean_SUIT": w["SUIT"].mean(),
                         "mean_diff": mean, "ci_low": lo, "ci_high": hi, "statistic": stat, "p": p,
                         "effect": rank_biserial_paired(diff), "effect_name": "matched-pairs rank-biserial r",
                         "cohens_dz": mean / diff.std(ddof=1) if diff.std(ddof=1) > 0 else np.nan})
        for value in ("rating_breach", "equity_over_cap", "holding_period_breach", "loss_tolerance_breach"):
            if value not in mm:
                continue
            w = paired(mm, value).astype(bool)
            if len(w) < 5:
                continue
            table = pd.crosstab(w["BASE"], w["SUIT"]).reindex(index=[False, True], columns=[False, True],
                                                              fill_value=0)
            b, c = table.loc[True, False], table.loc[False, True]
            res = mcnemar(table.values, exact=(b + c) < 25)
            rows.append({"model": mk, "outcome": value, "test": "McNemar" + (" (exact)" if (b + c) < 25 else ""),
                         "n_pairs": len(w), "mean_BASE": 100 * w["BASE"].mean(), "mean_SUIT": 100 * w["SUIT"].mean(),
                         "mean_diff": 100 * (w["SUIT"].mean() - w["BASE"].mean()), "statistic": res.statistic,
                         "p": res.pvalue, "effect": (c + 0.5) / (b + 0.5),
                         "effect_name": "discordant odds ratio SUIT/BASE (0.5-corrected)",
                         "discordant_base_only": b, "discordant_suit_only": c})
    t = pd.DataFrame(rows)
    if len(t):
        t["p_holm"] = holm(t["p"])
    return t


def t_model_comparison(m: pd.DataFrame) -> pd.DataFrame:
    models = sorted(m["model_key"].unique())
    rows = []
    if len(models) < 2:
        return pd.DataFrame()
    for c in sorted(m["condition"].unique()):
        mc = m[m["condition"] == c]
        w = mc.pivot_table(index="unit_id", columns="model_key", values="equity_pct", aggfunc="first").dropna()
        if len(models) >= 3 and len(w) > 5:
            chi2, p = stats.friedmanchisquare(*[w[k] for k in models])
            rows.append({"condition": c, "outcome": "equity_pct", "test": "Friedman", "n": len(w),
                         "statistic": chi2, "p": p, "effect": chi2 / (len(w) * (len(models) - 1)),
                         "effect_name": "Kendall's W"})
        for a, b in combinations(models, 2):
            stat, p = stats.wilcoxon(w[a], w[b])
            rows.append({"condition": c, "outcome": "equity_pct", "test": f"Wilcoxon {a} vs {b}", "n": len(w),
                         "statistic": stat, "p": p, "effect": rank_biserial_paired((w[a] - w[b]).to_numpy()),
                         "effect_name": "matched-pairs rank-biserial r", "mean_diff": (w[a] - w[b]).mean()})
        wb = mc.pivot_table(index="unit_id", columns="model_key", values="rating_breach", aggfunc="first").dropna()
        varies = (wb[models].astype(int).nunique(axis=1) > 1).any() if len(wb) else False
        if len(models) >= 3 and len(wb) > 5 and varies:  # Q is undefined when no investor differs
            q = cochrans_q(wb[models].astype(int).to_numpy())
            rows.append({"condition": c, "outcome": "rating_breach", "test": "Cochran's Q", "n": len(wb),
                         "statistic": q.statistic, "p": q.pvalue})
    t = pd.DataFrame(rows)
    t["p_holm"] = holm(t["p"])
    return t


def jaccard(a: str, b: str) -> float:
    sa, sb = set(str(a).split(";")) - {"", "nan"}, set(str(b).split(";")) - {"", "nan"}
    return len(sa & sb) / len(sa | sb) if sa | sb else np.nan


def t_consistency(d) -> pd.DataFrame:
    cons = d["cons"]
    sub_ids = set(cons.loc[cons["sample"] == "consistency", "unit_id"])
    cons = cons[cons["unit_id"].isin(sub_ids)]
    rows = []
    for mk, c, g in cells(cons):
        g = g.dropna(subset=["equity_pct"])
        full = g.groupby("unit_id").filter(lambda x: x["replicate"].nunique() == 3)
        if full["unit_id"].nunique() < 5:
            continue
        icc = pg.intraclass_corr(data=full, targets="unit_id", raters="replicate", ratings="equity_pct")
        # one-way random-effects, single rater: labelled "ICC1" (pingouin < 0.7) or "ICC(1,1)"
        icc = icc.set_index("Type").rename(index={"ICC(1,1)": "ICC1"}, columns={"CI95": "CI95%"})
        icc1 = icc.loc["ICC1"]
        sd = full.groupby("unit_id")["equity_pct"].std(ddof=1)
        jac, agree = [], []
        for _, u in full.groupby("unit_id"):
            sets = u.sort_values("replicate")["fund_set"].tolist()
            jac.append(np.mean([jaccard(x, y) for x, y in combinations(sets, 2)]))
            agree.append(u["rating_breach"].nunique() == 1)
        rows.append({"model": mk, "condition": c, "n_investors": full["unit_id"].nunique(),
                     "icc1_equity": icc1["ICC"], "icc1_ci95": str(icc1["CI95%"]),
                     "mean_within_sd_equity": sd.mean(), "max_within_sd_equity": sd.max(),
                     "mean_jaccard_fund_sets": float(np.mean(jac)),
                     "share_identical_fund_sets": float(np.mean([j == 1 for j in jac])),
                     "breach_flag_agreement": float(np.mean(agree))})
    return pd.DataFrame(rows)


def expand_probes(probe_res: pd.DataFrame) -> pd.DataFrame:
    p = pd.read_csv(ROOT / "data" / "probe_profiles.csv")
    keep = ["probe_id", "probe_text_id", "anchor_id", "varied_attribute", "risk_level", "horizon_band", "age_band"]
    out = p[keep].merge(probe_res.drop(columns=["risk_level", "horizon_band", "age_band"], errors="ignore"),
                        left_on="probe_text_id", right_on="unit_id", how="inner")
    out["horizon_level"] = out["horizon_band"].map(H_ORD)
    out["age_level"] = out["age_band"].map(A_ORD)
    return out


def t_sensitivity(d) -> pd.DataFrame:
    if d["probe"].empty:
        return pd.DataFrame()
    pr = expand_probes(d["probe"])
    level = {"risk": "risk_level", "horizon": "horizon_level", "age": "age_level"}
    rows = []
    for (mk, c), g in pr.groupby(["model_key", "condition"]):
        for attr, col in level.items():
            slopes, rhos, reversals = [], [], []
            for anchor, ga in g.groupby("anchor_id"):
                s = ga[(ga["varied_attribute"] == attr) | (ga["varied_attribute"] == "anchor")]
                s = s.dropna(subset=["equity_pct"]).sort_values(col)
                if s[col].nunique() < 3:
                    continue
                slopes.append(np.polyfit(s[col], s["equity_pct"], 1)[0])
                rhos.append(stats.spearmanr(s[col], s["equity_pct"])[0])
                step = np.diff(s["equity_pct"].to_numpy())
                expected = -1 if attr == "age" else 1
                reversals.append(int(np.sum(np.sign(step) == -expected)))
            if slopes:
                rows.append({"model": mk, "condition": c, "attribute": attr, "n_anchors": len(slopes),
                             "mean_slope_pp_per_step": np.mean(slopes), "sd_slope": np.std(slopes, ddof=1),
                             "mean_spearman_within_anchor": np.nanmean(rhos),
                             "anchors_with_expected_sign": int(np.sum(np.sign(slopes) ==
                                                                       (-1 if attr == "age" else 1))),
                             "mean_reversals_per_anchor": np.mean(reversals)})
    return pd.DataFrame(rows)


def t_conflict(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mk, c, g in cells(m):
        conf = g[g["profile_risk_horizon_conflict"]]
        aggressive_long = g[(g["risk_level"] >= 4) & (g["horizon_level"] >= 4)]
        for label, grp in (("C4-C5 with horizon < 3 years (conflict)", conf),
                           ("C4-C5 with horizon >= 5 years (no conflict)", aggressive_long)):
            rows.append({"model": mk, "condition": c, "group": label, "n": len(grp),
                         "mean_equity": grp["equity_pct"].mean(),
                         "equity_over_cap_pct": 100 * grp["equity_over_cap"].astype(float).mean(),
                         "mentions_conflict_terms_pct": 100 * grp["mentions_conflict_terms"].astype(float).mean(),
                         "mentions_horizon_pct": 100 * grp["mentions_horizon"].astype(float).mean(),
                         "conflicts_listed_pct": 100 * (grp["n_conflicts_listed"] > 0).mean()
                         if c == "SUIT" else np.nan,
                         "mean_risk_warnings": grp["n_risk_warnings"].mean()})
    return pd.DataFrame(rows)


def t_risk_class_assessment(m: pd.DataFrame) -> pd.DataFrame:
    s = m[(m["condition"] == "SUIT") & m["risk_class_assessed"].notna() & (m["risk_class_assessed"] != "")]
    rows = []
    for mk, g in s.groupby("model_key"):
        est = g["risk_class_assessed"].str[1].astype(int)
        true = g["risk_level"].astype(int)
        cm = pd.crosstab(true, est).reindex(index=range(1, 6), columns=range(1, 6), fill_value=0).to_numpy()
        n = cm.sum()
        wts = np.array([[(i - j) ** 2 for j in range(5)] for i in range(5)]) / 16
        expct = np.outer(cm.sum(1), cm.sum(0)) / n
        kappa_w = 1 - (wts * cm).sum() / (wts * expct).sum()
        rows.append({"model": mk, "n": len(g), "exact_agreement_pct": 100 * (est == true).mean(),
                     "within_one_pct": 100 * ((est - true).abs() <= 1).mean(),
                     "mean_signed_diff": (est - true).mean(), "quadratic_weighted_kappa": kappa_w})
    return pd.DataFrame(rows)


def t_qdii(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for mk, c, g in cells(m):
        for factor in ("risk_level", "horizon_level", "age_level"):
            x = g[[factor, "share_qdii"]].dropna()
            rho, p = stats.spearmanr(x[factor], x["share_qdii"])
            rows.append({"model": mk, "condition": c, "factor": factor, "mean_qdii_share": x["share_qdii"].mean(),
                         "share_with_any_qdii_pct": 100 * (x["share_qdii"] > 0).mean(), "rho": rho, "p": p})
    t = pd.DataFrame(rows)
    t["p_holm"] = holm(t["p"])
    return t


def t_robustness(d) -> pd.DataFrame:
    m = d["main"]
    rows = []
    variants = {
        "primary": m,
        "exclude repaired/extracted parses": m[m["parse_status"].isin(["ok", "fenced"])],
        "exclude replies with off-menu funds": m[m["off_menu_count"] == 0],
        "exclude replies with invalid weight sums": m[m["weight_sum_ok"].astype(bool)],
    }
    for name, g in variants.items():
        for mk, c, gg in cells(g):
            x = gg.dropna(subset=["equity_pct"])
            rows.append({"variant": name, "model": mk, "condition": c, "n": len(x),
                         "rho_equity_risk": stats.spearmanr(x["risk_level"], x["equity_pct"])[0],
                         "rho_equity_horizon": stats.spearmanr(x["horizon_level"], x["equity_pct"])[0],
                         "rho_equity_age": stats.spearmanr(x["age_level"], x["equity_pct"])[0],
                         "rating_breach_pct": 100 * x["rating_breach"].astype(float).mean(),
                         "rating_breach_over5pct_weight_pct": 100 * (x["rating_breach_weight"] > 5).mean()})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ main --

def run(out_root: Path = ROOT / "outputs") -> dict:
    d = load(out_root)
    tables = out_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    m = d["main"]
    out = {
        "T04_feasibility_and_behaviour": t_feasibility(d, out_root / "raw"),
        "T05_equity_by_risk_class": t_means_by_factor(m, "risk_class"),
        "T06_equity_by_horizon": t_means_by_factor(m, "horizon_band"),
        "T07_equity_by_age_band": t_means_by_factor(m, "age_band"),
        "T08_spearman_attribute_alignment": t_spearman(m),
        "T09_anova_partial_eta_squared": t_anova(m),
        "T10_pooled_regression_cluster_se": t_pooled_regression(m),
        "T11_suitability_by_model_condition": t_suitability(m, ["model_key", "condition"]),
        "T12_suitability_by_risk_class": t_suitability(m, ["model_key", "condition", "risk_class"]),
        "T13_condition_effects_paired": t_condition_effects(m),
        "T14_model_comparison": t_model_comparison(m),
        "T15_consistency_repeated_queries": t_consistency(d),
        "T16_single_attribute_sensitivity": t_sensitivity(d),
        "T17_conflict_handling": t_conflict(m),
        "T18_risk_class_assessment_SUIT": t_risk_class_assessment(m),
        "T19_qdii_allocation": t_qdii(m),
        "T20_robustness": t_robustness(d),
        "T21_regression_with_covariates": t_pooled_regression(m, covariates=True),
    }
    digest = ["# Results digest (generated by src/analysis.py - do not edit by hand)", "",
              f"Main-sample coded replies: {len(m)}; units: {m['unit_id'].nunique()}; "
              f"models: {', '.join(sorted(m['model_key'].unique()))}", ""]
    for name, t in out.items():
        t.to_csv(tables / f"{name}.csv", index=False)
        digest += [f"## {name}", "", t.round(4).to_markdown(index=False) if len(t) else "(no data)", ""]
    (tables / "results_digest.md").write_text("\n".join(digest), encoding="utf-8")
    print(f"Wrote {len(out)} tables to {tables}")
    return out


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
