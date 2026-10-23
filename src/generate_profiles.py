"""Generate the SYNTHETIC investor samples used in the experiment.

Outputs
-------
data/investor_profiles.csv  200 unique investors, one per cell of the
                            5 (horizon) x 5 (risk tolerance) x 8 (age) design.
data/probe_profiles.csv     single-attribute probe set: 10 anchor investors,
                            each re-stated with exactly one attribute changed.

Sampling design
---------------
* Main sample: balanced full factorial. Every combination of the three
  independent variables occurs exactly once, so the three factors are
  orthogonal (uncorrelated) by construction.
* Within each cell, the exact age, the exact horizon, and the secondary
  attributes (objective wording, employment, experience, amount) are drawn
  with a fixed random seed, subject to the consistency rules below.
* Investor IDs are assigned after shuffling, so the ID carries no information
  about the profile's attributes.

Consistency rules (checked again by validate_profiles.py)
---------------------------------------------------------
* Employment depends on age (students only under 22; retirees only 60+).
* Investment experience cannot exceed (age - 18) years.
* The investment objective depends on horizon and age (no retirement-income
  objective before 50; legacy objective only from 65 and only for horizons
  of 10+ years; near-term spending objectives only for horizons under 1 year).
* Liquidity need follows the horizon.

Run:  python src/generate_profiles.py [--seed 20261022]
"""

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

from design import AGE_BANDS, HORIZONS, RISK_CLASSES, format_horizon

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_SEED = 20261022

# Investable amount ranges (CNY) by age band; drawn log-uniformly.
AMOUNT_RANGE = {
    "A1": (20_000, 100_000), "A2": (50_000, 300_000), "A3": (100_000, 800_000),
    "A4": (100_000, 1_000_000), "A5": (150_000, 1_200_000), "A6": (150_000, 1_200_000),
    "A7": (100_000, 1_000_000), "A8": (100_000, 800_000),
}

LIQUIDITY = {"H1": "High", "H2": "Moderate", "H3": "Moderate", "H4": "Low", "H5": "Low"}
LIQUIDITY_TEXT = {
    "High": "high - I will need to withdraw most of this money at the end of the horizon",
    "Moderate": "moderate - I will withdraw the money when the goal falls due",
    "Low": "low - no withdrawals are planned before the end of the horizon",
}

EXPERIENCE_LEVELS = (("No experience", 0, 0), ("Limited", 1, 3), ("Moderate", 4, 9), ("Extensive", 10, 30))


def objective_for(h_code: str, age: int, rng) -> tuple[str, str]:
    """Return (objective_category, objective_text) consistent with horizon and age."""
    if h_code == "H1":
        if age <= 34:
            options = ["set aside money for a planned purchase this year, such as a car",
                       "keep money ready for wedding expenses later this year"]
        elif age <= 64:
            options = ["hold money for a home renovation planned within the year",
                       "keep funds ready for a child's tuition payment due within the year"]
        else:
            options = ["keep money available for planned medical and family expenses within the year",
                       "hold money for a family member's planned expense within the year"]
        return "Near-term spending", rng.choice(options)
    if h_code == "H2":
        if age <= 44:
            options = ["save for a home down payment", "save for a planned car purchase and moving costs"]
        elif age <= 64:
            options = ["save for a child's wedding", "save for a planned home upgrade"]
        else:
            options = ["fund planned travel and support for family members over the next few years",
                       "pay for planned home adaptations for later life"]
        return "Short-term goal", rng.choice(options)
    if h_code == "H3":
        if age <= 24:
            return "Medium-term goal", rng.choice(["save for postgraduate study",
                                                   "build savings toward a future home deposit"])
        if age <= 54:
            return "Medium-term goal", rng.choice(["save for a child's education", "save for a larger home"])
        if age <= 64:
            return "Retirement preparation", "build a reserve to cover the first years of retirement"
        return "Retirement income", "supplement my pension over the next few years"
    if h_code == "H4":
        if age <= 54:
            return "Wealth accumulation", rng.choice(["build long-term wealth",
                                                      "grow my savings for future family needs"])
        if age <= 64:
            return "Retirement income", "build savings to supplement my pension in retirement"
        return "Retirement income", "supplement my pension later in retirement"
    # H5
    if age <= 49:
        return "Retirement accumulation", "accumulate savings for retirement"
    if age <= 64:
        return "Retirement income", "fund a long retirement"
    return "Legacy", "build a legacy for my children or grandchildren"


def employment_for(age: int, rng) -> tuple[str, str]:
    """Return (employment_status, income_stability)."""
    if age <= 21:
        return "University student with part-time income", "Variable"
    if age <= 24:
        return "Early-career salaried employee", "Stable"
    if age <= 59:
        if rng.random() < 0.2:
            return "Self-employed", "Variable"
        return "Salaried employee", "Stable"
    if age <= 64:
        if rng.random() < 0.5:
            return "Retired, receives a pension", "Stable"
        return "Salaried employee, planning to retire within a few years", "Stable"
    return "Retired, receives a pension", "Stable"


def experience_for(age: int, rng) -> tuple[str, int]:
    max_years = min(age - 18, 30)
    feasible = [lvl for lvl in EXPERIENCE_LEVELS if lvl[1] <= max_years]
    name, lo, hi = feasible[rng.integers(len(feasible))]
    years = int(rng.integers(lo, min(hi, max_years) + 1))
    return name, years


def amount_for(age_code: str, rng) -> int:
    lo, hi = AMOUNT_RANGE[age_code]
    value = math.exp(rng.uniform(math.log(lo), math.log(hi)))
    step = 5_000 if age_code == "A1" else 10_000
    return int(round(value / step) * step)


def experience_text(years: int) -> str:
    if years == 0:
        return "no previous investment experience"
    unit = "year" if years == 1 else "years"
    return (f"{years} {unit} of experience with mutual funds and bank "
            f"wealth-management products")


def render_profile(p: dict) -> str:
    """Render the investor description exactly as the model will see it."""
    risk = next(r for r in RISK_CLASSES if r.code == p["risk_class"])
    lines = [
        f"Age: {p['age']}",
        f"Employment and income: {p['employment_status']} ({p['income_stability'].lower()} income)",
        f"Amount to invest: CNY {p['investable_amount_cny']:,}",
        f"Investment objective: I want to {p['objective_text']}.",
        f"Investment horizon: {format_horizon(p['horizon_years'])}; I do not expect to withdraw this money before then.",
        f"Liquidity need: {LIQUIDITY_TEXT[p['liquidity_need']]}.",
        (f"Risk tolerance: {risk.label}. {risk.max_one_year_loss}. My priority is "
         f"{risk.priority}. If the stock market fell by 20%, I would {risk.reaction_to_20pct_fall}."),
        f"Investment experience: {experience_text(p['experience_years'])}.",
        "Emergency savings: kept separately and not part of this investment.",
    ]
    return "\n".join(lines)


def build_main_sample(rng) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        for r in RISK_CLASSES:
            for a in AGE_BANDS:
                age = int(rng.integers(a.lower, a.upper + 1))
                options = list(h.stated_values)
                if h.code == "H5" and a.code == "A8":
                    options = [v for v in options if v <= 15]
                elif h.code == "H5" and a.code == "A7":
                    options = [v for v in options if v <= 20]
                horizon_years = float(rng.choice(options))
                obj_cat, obj_text = objective_for(h.code, age, rng)
                emp, inc = employment_for(age, rng)
                exp_level, exp_years = experience_for(age, rng)
                rows.append({
                    "cell_id": f"{h.code}-{r.code}-{a.code}",
                    "age": age, "age_band": a.code, "age_band_label": a.label,
                    "life_stage": a.life_stage,
                    "horizon_years": horizon_years, "horizon_band": h.code, "horizon_label": h.label,
                    "risk_class": r.code, "risk_level": r.level, "risk_label": r.label,
                    "objective_category": obj_cat, "objective_text": obj_text,
                    "liquidity_need": LIQUIDITY[h.code],
                    "employment_status": emp, "income_stability": inc,
                    "experience_level": exp_level, "experience_years": exp_years,
                    "investable_amount_cny": amount_for(a.code, rng),
                    "emergency_savings": "Held separately",
                })
    df = pd.DataFrame(rows)
    df = df.sample(frac=1.0, random_state=int(rng.integers(1_000_000))).reset_index(drop=True)
    df.insert(0, "investor_id", [f"INV-{i:03d}" for i in range(1, len(df) + 1)])
    df["profile_text"] = [render_profile(row) for row in df.to_dict("records")]
    return df


def flag_consistency_subsample(df: pd.DataFrame, rng, per_class: int = 8) -> pd.DataFrame:
    """Stratified random subsample (8 per risk class = 40) for repeated queries."""
    chosen = []
    for code in sorted(df["risk_class"].unique()):
        ids = df.loc[df["risk_class"] == code, "investor_id"].tolist()
        chosen += list(rng.choice(ids, size=per_class, replace=False))
    df["in_consistency_subsample"] = df["investor_id"].isin(chosen)
    return df


# ---------------------------------------------------------------------------
# Probe set: one attribute changed at a time, everything else held constant.
# Secondary attributes use neutral wording that is valid for every age,
# horizon and risk level, so no variant is internally inconsistent.
# ---------------------------------------------------------------------------

def render_probe(age: int, horizon_years: float, risk_code: str) -> str:
    risk = next(r for r in RISK_CLASSES if r.code == risk_code)
    lines = [
        f"Age: {age}",
        "Employment and income: stable regular income (salary or pension)",
        "Amount to invest: CNY 200,000",
        "Investment objective: I want to invest savings that are not needed for everyday spending.",
        f"Investment horizon: {format_horizon(horizon_years)}; I do not expect to withdraw this money before then.",
        (f"Risk tolerance: {risk.label}. {risk.max_one_year_loss}. My priority is "
         f"{risk.priority}. If the stock market fell by 20%, I would {risk.reaction_to_20pct_fall}."),
        "Investment experience: some experience with mutual funds.",
        "Emergency savings: kept separately and not part of this investment.",
    ]
    return "\n".join(lines)


def build_probe_set(rng, n_anchors: int = 10) -> pd.DataFrame:
    risk_seq = rng.permutation([r.code for r in RISK_CLASSES] * 2)
    hor_seq = rng.permutation([h.code for h in HORIZONS] * 2)
    age_codes = [a.code for a in AGE_BANDS]
    age_seq = rng.permutation(age_codes + list(rng.choice(age_codes, size=n_anchors - len(age_codes), replace=False)))
    rows = []
    for i in range(n_anchors):
        anchor = {"risk": risk_seq[i], "horizon": hor_seq[i], "age": age_seq[i]}
        variants = [("anchor", None)]
        variants += [("risk", r.code) for r in RISK_CLASSES if r.code != anchor["risk"]]
        variants += [("horizon", h.code) for h in HORIZONS if h.code != anchor["horizon"]]
        variants += [("age", a.code) for a in AGE_BANDS if a.code != anchor["age"]]
        for varied, value in variants:
            cfg = dict(anchor)
            if varied != "anchor":
                cfg[varied] = value
            h = next(x for x in HORIZONS if x.code == cfg["horizon"])
            a = next(x for x in AGE_BANDS if x.code == cfg["age"])
            r = next(x for x in RISK_CLASSES if x.code == cfg["risk"])
            suffix = "ANCHOR" if varied == "anchor" else f"{varied.upper()}-{value}"
            rows.append({
                "probe_id": f"PRB-{i + 1:02d}-{suffix}",
                "anchor_id": f"PRB-{i + 1:02d}",
                "varied_attribute": varied,
                "anchor_risk_class": anchor["risk"], "anchor_horizon_band": anchor["horizon"],
                "anchor_age_band": anchor["age"],
                "age": a.probe_age, "age_band": a.code, "horizon_years": h.probe_value,
                "horizon_band": h.code, "risk_class": r.code, "risk_level": r.level,
                "profile_text": render_probe(a.probe_age, h.probe_value, r.code),
            })
    df = pd.DataFrame(rows)
    # Different anchors can produce the same attribute combination; because the
    # secondary wording is neutral, those versions are textually identical. Each
    # distinct text gets one key and is queried once; results are shared by all
    # probe IDs carrying that key.
    keys = {t: f"PTX-{i:03d}" for i, t in enumerate(dict.fromkeys(df["profile_text"]), start=1)}
    df["probe_text_id"] = df["profile_text"].map(keys)
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)

    main_df = build_main_sample(rng)
    main_df = flag_consistency_subsample(main_df, rng)
    main_df.insert(1, "data_type", "SYNTHETIC investor profile")
    main_df["generator_seed"] = args.seed
    probe_df = build_probe_set(rng)
    probe_df.insert(1, "data_type", "SYNTHETIC probe profile")
    probe_df["generator_seed"] = args.seed

    DATA.mkdir(exist_ok=True)
    main_df.to_csv(DATA / "investor_profiles.csv", index=False, encoding="utf-8")
    probe_df.to_csv(DATA / "probe_profiles.csv", index=False, encoding="utf-8")
    print(f"Wrote {len(main_df)} main profiles and {len(probe_df)} probe profiles (seed {args.seed}).")


if __name__ == "__main__":
    main()
