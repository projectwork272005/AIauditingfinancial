"""Validate the synthetic investor samples and document their composition.

Checks (main sample)
  V01 exactly 200 rows                      V08 objective consistent with horizon and age
  V02 unique, well-formed investor IDs      V09 liquidity need consistent with horizon
  V03 no missing values                     V10 no duplicate profile texts
  V04 every 5x5x8 cell exactly once         V11 no duplicate attribute vectors (ignoring ID)
  V05 exact age inside its age band         V12 factors mutually independent (Cramer's V = 0)
  V06 stated horizon inside its band        V13 consistency subsample = 8 per risk class
  V07 experience <= age - 18; employment consistent with age
Checks (probe set)
  P01 160 rows, 16 per anchor               P03 unique probe IDs and texts
  P02 each variant differs from its anchor in exactly one attribute and one line

Writes docs/profile_validation_report.md and outputs/tables/T01-T03 CSVs.
Exit code 1 if any check fails.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from design import AGE_BANDS, HORIZONS, RISK_CLASSES, age_band_for, horizon_band_for

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["investor_id", "age", "age_band", "horizon_years", "horizon_band", "risk_class",
            "risk_level", "objective_category", "objective_text", "liquidity_need",
            "employment_status", "income_stability", "experience_level", "experience_years",
            "investable_amount_cny", "profile_text"]


def cramers_v(x, y) -> float:
    table = pd.crosstab(x, y)
    chi2 = chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    k = min(table.shape) - 1
    return float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0


def objective_ok(row) -> bool:
    cat, h, age = row["objective_category"], row["horizon_band"], row["age"]
    if cat == "Near-term spending":
        return h == "H1"
    if cat == "Short-term goal":
        return h == "H2"
    if cat == "Medium-term goal":
        return h == "H3" and age <= 54
    if cat == "Retirement preparation":
        return h == "H3" and 55 <= age <= 64
    if cat == "Wealth accumulation":
        return h == "H4" and age <= 54
    if cat == "Retirement accumulation":
        return h == "H5" and age <= 49
    if cat == "Retirement income":
        return age >= 50 and h in ("H3", "H4", "H5")
    if cat == "Legacy":
        return age >= 65 and h == "H5"
    return False


def employment_ok(row) -> bool:
    emp, age = row["employment_status"], row["age"]
    if emp.startswith("University student"):
        return age <= 21
    if emp.startswith("Retired"):
        return age >= 60
    if emp.startswith("Early-career"):
        return 22 <= age <= 24
    if emp.startswith("Salaried employee, planning"):
        return 60 <= age <= 64
    return 25 <= age <= 59  # salaried / self-employed


def run_main_checks(df: pd.DataFrame) -> list[tuple[str, str, bool, str]]:
    res = []
    res.append(("V01", "Exactly 200 profiles", len(df) == 200, f"rows = {len(df)}"))
    ids_ok = df["investor_id"].is_unique and df["investor_id"].str.fullmatch(r"INV-\d{3}").all()
    res.append(("V02", "Unique, well-formed investor IDs", bool(ids_ok),
                f"unique IDs = {df['investor_id'].nunique()}"))
    missing = int(df[REQUIRED].isna().sum().sum())
    res.append(("V03", "No missing values in required fields", missing == 0, f"missing cells = {missing}"))
    cells = df.groupby(["horizon_band", "risk_class", "age_band"]).size()
    full = (len(cells) == 200) and (cells == 1).all()
    res.append(("V04", "Every horizon x risk x age cell exactly once (5 x 5 x 8)", bool(full),
                f"distinct cells = {len(cells)}; max per cell = {cells.max()}"))
    age_ok = all(age_band_for(a).code == b for a, b in zip(df["age"], df["age_band"]))
    res.append(("V05", "Exact age lies inside stated age band", age_ok,
                f"age range {df['age'].min()}-{df['age'].max()}"))
    hor_ok = all(horizon_band_for(y).code == b for y, b in zip(df["horizon_years"], df["horizon_band"]))
    res.append(("V06", "Stated horizon lies inside its horizon band", hor_ok,
                f"horizon range {df['horizon_years'].min()}-{df['horizon_years'].max()} years"))
    exp_ok = (df["experience_years"] <= df["age"] - 18).all()
    emp_ok = df.apply(employment_ok, axis=1).all()
    res.append(("V07", "Experience <= age - 18 and employment consistent with age",
                bool(exp_ok and emp_ok), f"experience ok = {bool(exp_ok)}; employment ok = {bool(emp_ok)}"))
    obj_ok = df.apply(objective_ok, axis=1)
    res.append(("V08", "Objective consistent with horizon and age", bool(obj_ok.all()),
                f"violations = {int((~obj_ok).sum())}"))
    liq_map = {"H1": "High", "H2": "Moderate", "H3": "Moderate", "H4": "Low", "H5": "Low"}
    liq_ok = (df["horizon_band"].map(liq_map) == df["liquidity_need"]).all()
    res.append(("V09", "Liquidity need consistent with horizon", bool(liq_ok), ""))
    res.append(("V10", "No duplicate profile texts", df["profile_text"].is_unique,
                f"distinct texts = {df['profile_text'].nunique()}"))
    attr = df.drop(columns=["investor_id", "profile_text"], errors="ignore")
    res.append(("V11", "No duplicate attribute vectors (ignoring ID)", not attr.duplicated().any(), ""))
    vs = {f"{a}~{b}": cramers_v(df[a], df[b]) for a, b in
          [("horizon_band", "risk_class"), ("horizon_band", "age_band"), ("risk_class", "age_band")]}
    res.append(("V12", "Independent variables mutually independent (Cramer's V)",
                all(v < 1e-9 for v in vs.values()), "; ".join(f"{k} = {v:.3f}" for k, v in vs.items())))
    sub = df[df["in_consistency_subsample"]]
    sub_ok = len(sub) == 40 and (sub["risk_class"].value_counts() == 8).all()
    res.append(("V13", "Consistency subsample: 40 investors, 8 per risk class", bool(sub_ok),
                f"subsample size = {len(sub)}"))
    return res


def run_probe_checks(p: pd.DataFrame) -> list[tuple[str, str, bool, str]]:
    res = []
    sizes = p.groupby("anchor_id").size()
    res.append(("P01", "160 probe rows, 16 per anchor", len(p) == 160 and (sizes == 16).all(),
                f"rows = {len(p)}; anchors = {len(sizes)}"))
    bad = 0
    for _, grp in p.groupby("anchor_id"):
        anchor = grp[grp["varied_attribute"] == "anchor"].iloc[0]
        a_lines = anchor["profile_text"].split("\n")
        for _, row in grp[grp["varied_attribute"] != "anchor"].iterrows():
            diffs = [c for c in ("age_band", "horizon_band", "risk_class") if row[c] != anchor[c]]
            lines = row["profile_text"].split("\n")
            changed = sum(1 for x, y in zip(lines, a_lines) if x != y)
            if len(diffs) != 1 or changed != 1 or len(lines) != len(a_lines):
                bad += 1
    res.append(("P02", "Each variant differs from its anchor in exactly one attribute (one line)",
                bad == 0, f"violations = {bad}"))
    one_text_per_key = (p.groupby("probe_text_id")["profile_text"].nunique() == 1).all()
    one_key_per_text = (p.groupby("profile_text")["probe_text_id"].nunique() == 1).all()
    res.append(("P03", "Unique probe IDs; one text key per distinct text",
                bool(p["probe_id"].is_unique and one_text_per_key and one_key_per_text),
                f"distinct probe texts = {p['probe_text_id'].nunique()} (shared across anchors where "
                "attribute combinations coincide)"))
    return res


def distribution_tables(df: pd.DataFrame):
    out = ROOT / "outputs" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    marg = []
    for var, cats in [("horizon_band", HORIZONS), ("risk_class", RISK_CLASSES), ("age_band", AGE_BANDS)]:
        counts = df[var].value_counts()
        for c in cats:
            label = getattr(c, "label")
            marg.append({"variable": var, "code": c.code, "label": label,
                         "n": int(counts.get(c.code, 0)), "percent": 100 * counts.get(c.code, 0) / len(df)})
    t1 = pd.DataFrame(marg)
    t1.to_csv(out / "T01_sample_marginal_distribution.csv", index=False)
    t2 = pd.crosstab(df["age_band"], df["objective_category"])
    t2.to_csv(out / "T02_objective_by_age_band.csv")
    t3 = df.groupby("age_band").agg(
        n=("investor_id", "size"), mean_age=("age", "mean"),
        median_amount_cny=("investable_amount_cny", "median"),
        mean_experience_years=("experience_years", "mean"),
        share_stable_income=("income_stability", lambda s: (s == "Stable").mean()),
        share_retired=("employment_status", lambda s: s.str.startswith("Retired").mean()),
    ).round(2)
    t3.to_csv(out / "T03_secondary_attributes_by_age_band.csv")
    return t1, t2, t3


def main() -> int:
    df = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    probes = pd.read_csv(ROOT / "data" / "probe_profiles.csv")
    checks = run_main_checks(df) + run_probe_checks(probes)
    t1, t2, t3 = distribution_tables(df)

    lines = ["# Investor Profile Validation Report", "",
             "All profiles are **synthetic**. Generated by `src/generate_profiles.py` "
             f"(seed {int(df['generator_seed'].iloc[0])}); validated by `src/validate_profiles.py`.", "",
             "## Checks", "", "| ID | Check | Result | Detail |", "|---|---|---|---|"]
    for cid, desc, ok, detail in checks:
        lines.append(f"| {cid} | {desc} | {'PASS' if ok else 'FAIL'} | {detail} |")
    lines += ["", "## Marginal distribution of the independent variables (main sample, N = 200)", "",
              "| Variable | Code | Label | n | % |", "|---|---|---|---|---|"]
    for r in t1.itertuples():
        lines.append(f"| {r.variable} | {r.code} | {r.label} | {r.n} | {r.percent:.1f} |")
    lines += ["", "Each horizon x risk cell contains 8 investors (one per age band); each horizon x age "
              "cell and each risk x age cell contains 5 investors.", "",
              "## Investment objective by age band", "", t2.to_markdown(), "",
              "## Secondary attributes by age band", "", t3.to_markdown(), "",
              "## Probe set", "",
              f"{len(probes)} probe profiles ({probes['probe_text_id'].nunique()} distinct texts): "
              f"{probes['anchor_id'].nunique()} anchors x 16 versions "
              "(the anchor, 4 alternative risk classes, 4 alternative horizons, 7 alternative age bands). "
              "Secondary attributes use neutral wording held constant across all versions.", ""]
    report = ROOT / "docs" / "profile_validation_report.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    failed = [c for c in checks if not c[2]]
    for cid, desc, ok, detail in checks:
        print(f"{cid} {'PASS' if ok else 'FAIL'}  {desc}  {detail}")
    print(f"\nReport: {report.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
