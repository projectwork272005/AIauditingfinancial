"""Supplementary descriptive tables cited in the report text (Section 9).

Reads only the coded results and the back-test written by the pipeline, so every
number quoted in the report can be regenerated:

  T22_rating_breach_c1_c3.csv      rating breach among C1-C3 investors (the only
                                   classes that can breach, because no menu fund is R5)
  T23_rating_breach_composition.csv  highest rating held in breaching replies, by class
  T24_backtest_by_risk_class.csv   back-test summary of main-sample portfolios

Run: python report/report_supplement.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"


def main() -> None:
    res = pd.read_csv(ROOT / "outputs" / "experiment_results.csv", dtype={"unit_id": str})
    main_s = res[(res["sample"] == "main") & (res["portfolio_codable"] == True)].copy()  # noqa: E712
    main_s["rating_breach"] = main_s["rating_breach"].astype(bool)

    low = main_s[main_s["risk_class"].isin(["C1", "C2", "C3"])]
    by_cell = (low.groupby(["model_key", "condition"])
               .agg(n=("call_id", "size"), rating_breach_pct=("rating_breach", "mean")).reset_index())
    pooled = (low.groupby("condition")
              .agg(n=("call_id", "size"), rating_breach_pct=("rating_breach", "mean")).reset_index())
    pooled.insert(0, "model_key", "all")
    t22 = pd.concat([by_cell, pooled], ignore_index=True)
    t22["rating_breach_pct"] = (100 * t22["rating_breach_pct"]).round(1)
    t22.to_csv(TABLES / "T22_rating_breach_c1_c3.csv", index=False)

    br = low[low["rating_breach"]]
    comp = (br.groupby(["risk_class", "max_risk"]).size().rename("n_replies").reset_index())
    comp["max_rating_held"] = "R" + comp["max_risk"].astype(int).astype(str)
    comp["share_of_breaches_pct"] = (100 * comp["n_replies"]
                                     / comp.groupby("risk_class")["n_replies"].transform("sum")).round(1)
    w = (br.groupby(["risk_class"])["rating_breach_weight"].mean().round(1)
         .rename("mean_breach_weight_pct").reset_index())
    comp = comp.merge(w, on="risk_class")[["risk_class", "max_rating_held", "n_replies",
                                           "share_of_breaches_pct", "mean_breach_weight_pct"]]
    comp.to_csv(TABLES / "T23_rating_breach_composition.csv", index=False)

    bt = pd.read_csv(ROOT / "outputs" / "portfolio_backtest.csv")
    x = main_s.merge(bt, on="call_id", how="inner")
    x["loss_tolerance_breach"] = x["loss_tolerance_breach"].astype(bool)
    t24 = (x.groupby(["condition", "risk_class"])
           .agg(n=("call_id", "size"),
                max_loss_tolerated_pct=("max_loss_tolerated_pct", "first"),
                median_worst_12m_pct=("worst_12m_pct", "median"),
                min_worst_12m_pct=("worst_12m_pct", "min"),
                median_max_drawdown_pct=("max_drawdown_pct", "median"),
                median_cagr_pct=("cagr_pct", "median"),
                loss_tolerance_breach_pct=("loss_tolerance_breach", "mean"),
                window=("window", "first"))
           .reset_index())
    t24["loss_tolerance_breach_pct"] = 100 * t24["loss_tolerance_breach_pct"]
    num = t24.select_dtypes("number").columns.drop("n")
    t24[num] = t24[num].round(2)
    t24.to_csv(TABLES / "T24_backtest_by_risk_class.csv", index=False)

    suit = low[low["condition"] == "SUIT"].copy()
    suit["classified_correctly"] = suit["risk_class_assessed"] == suit["risk_class"]
    t25 = (suit.groupby(["model_key", "classified_correctly"])
           .agg(n=("call_id", "size"), rating_breach_pct=("rating_breach", "mean")).reset_index())
    t25["rating_breach_pct"] = (100 * t25["rating_breach_pct"]).round(1)
    t25.to_csv(TABLES / "T25_suit_breach_by_classification_c1_c3.csv", index=False)

    perf_path = ROOT / "outputs" / "portfolio_performance.csv"
    if perf_path.exists():                      # written by src/performance.py
        perf = pd.read_csv(perf_path)
        y = main_s.merge(perf, on="call_id", how="inner")
        y = y[y["risk_class"].isin(["C1", "C2"])]
        t32 = (y.groupby(["risk_class", "rating_breach"])
               .agg(n=("call_id", "size"), median_cagr_pct=("cagr_pct", "median"),
                    median_vol_pct=("vol_pct", "median"), median_max_drawdown_pct=("max_drawdown_pct", "median"))
               .reset_index().round(3))
        t32.to_csv(TABLES / "T32_return_by_rating_breach_c1_c2.csv", index=False)
    cons_path = ROOT / "outputs" / "manual_coding_consensus.csv"
    if cons_path.exists():                      # written by src/manual_coding.py finalize
        cons = pd.read_csv(cons_path)
        z = cons.merge(res[["call_id", "model_key", "condition", "profile_risk_horizon_conflict"]], on="call_id")
        z["group"] = z["profile_risk_horizon_conflict"].map({True: "C4-C5, horizon < 3 years",
                                                             False: "all other investors"})
        t34 = (z.groupby(["condition", "group", "model_key"])
               .agg(n=("call_id", "size"), conflict_acknowledged_pct=("consensus", "mean"),
                    keyword_rule_pct=("automated", "mean")).reset_index())
        t34[["conflict_acknowledged_pct", "keyword_rule_pct"]] = (100 * t34[["conflict_acknowledged_pct",
                                                                              "keyword_rule_pct"]]).round(1)
        t34.to_csv(TABLES / "T34_conflict_acknowledgement_double_coded.csv", index=False)
    print("Wrote T22-T25, T32 and T34 to", TABLES)


if __name__ == "__main__":
    main()
