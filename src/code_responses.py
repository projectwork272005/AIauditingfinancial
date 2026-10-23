"""Code raw model replies into the structured results dataset.

Input : outputs/raw/calls_<model>.jsonl (append-only API logs)
        data/fund_menu.csv, data/investor_profiles.csv, data/probe_profiles.csv
Output: outputs/experiment_results.csv   one row per successful call
        outputs/experiment_holdings.csv  one row per recommended fund
        outputs/coding_issues.csv        parse problems, off-menu codes, etc.

Coding is fully rule-based and deterministic, so rerunning it on the same
logs always gives the same dataset. The rules are documented in
docs/coding_sheet.md. Off-menu funds are counted as feasibility errors and
excluded (with renormalisation of the remaining weights) from the portfolio
risk measures; the raw weights are kept in the holdings file.
"""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from design import EQUITY_CAP_BY_RISK, RISK_CLASSES, suitable_equity_cap

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "outputs" / "raw"
WEIGHT_TOL = 1.0          # |sum - 100| <= 1 percentage point counts as a valid allocation
EQUITY_TOL = 5.0          # equity above the suitable cap by more than 5 pp counts as excess
CONFLICT_TERMS = re.compile(
    r"\b(conflict\w*|inconsisten\w*|mismatch\w*|contradict\w*|tension|at odds|"
    r"not (?:fully )?(?:compatible|consistent|aligned))\b", re.I)
HORIZON_TERMS = re.compile(
    r"\b(short(?:er)?[- ]term|short (?:investment )?horizon|within (?:a|one|1) year|"
    r"(?:\d+|few|several) months|time horizon|horizon)\b", re.I)


# ----------------------------------------------------------------------------
# Parsing
# ----------------------------------------------------------------------------

def extract_json(text: str):
    """Return (object, status). status: ok | fenced | extracted | repaired | failed."""
    if not isinstance(text, str) or not text.strip():
        return None, "failed"
    t = text.strip()
    try:
        return json.loads(t), "ok"
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.S)
    if fence:
        try:
            return json.loads(fence.group(1)), "fenced"
        except json.JSONDecodeError:
            pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        chunk = t[start:end + 1]
        try:
            return json.loads(chunk), "extracted"
        except json.JSONDecodeError:
            repaired = re.sub(r",\s*([}\]])", r"\1", chunk)  # trailing commas only
            try:
                return json.loads(repaired), "repaired"
            except json.JSONDecodeError:
                pass
    return None, "failed"


def to_number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if m:
            return float(m.group())
    return np.nan


def parse_portfolio(obj, menu_names: dict) -> list[dict]:
    items = obj.get("portfolio") if isinstance(obj, dict) else None
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        raw_code = str(it.get("code", "")).strip()
        m = re.search(r"\d{6}", raw_code)
        code, source = (m.group(), "code") if m else (None, None)
        name = str(it.get("fund_name", "")).strip()
        if code is None and name in menu_names:
            code, source = menu_names[name], "name"
        weight = np.nan
        for key in ("weight_pct", "weight", "allocation_pct", "allocation", "percentage"):
            if key in it:
                weight = to_number(it[key])
                break
        out.append({"code": code, "code_source": source, "raw_code": raw_code,
                    "fund_name_given": name, "weight_raw": weight})
    return out


# ----------------------------------------------------------------------------
# Coding
# ----------------------------------------------------------------------------

def normalize_holdings(hold: pd.DataFrame) -> pd.DataFrame:
    """On-menu funds with a positive weight, duplicates merged, weights rescaled
    to sum to 100. Returns columns code, w. Shared with backtest.py."""
    if hold.empty:
        return pd.DataFrame(columns=["code", "w"])
    on = hold[hold["on_menu"] & hold["weight_raw"].notna() & (hold["weight_raw"] > 0)]
    on = on.groupby("code", as_index=False)["weight_raw"].sum()
    total = on["weight_raw"].sum()
    if total <= 0:
        return pd.DataFrame(columns=["code", "w"])
    return on.assign(w=100 * on["weight_raw"] / total)[["code", "w"]]

def load_menu(path: Path = ROOT / "data" / "fund_menu.csv") -> pd.DataFrame:
    menu = pd.read_csv(path, dtype=str).fillna("")
    menu["risk_num"] = menu["risk_rating"].str.extract(r"R(\d)").astype(float)
    fallback = pd.to_numeric(menu["fallback_equity_pct"], errors="coerce")
    if "equity_exposure_pct" in menu:
        menu["equity_exposure"] = pd.to_numeric(menu["equity_exposure_pct"], errors="coerce").fillna(fallback)
    else:
        menu["equity_exposure"] = fallback
    menu["min_hold"] = pd.to_numeric(menu["min_holding_years"], errors="coerce").fillna(0)
    return menu.set_index("code")


def unit_attributes() -> pd.DataFrame:
    inv = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    inv = inv.rename(columns={"investor_id": "unit_id"})
    probes = pd.read_csv(ROOT / "data" / "probe_profiles.csv").drop_duplicates("probe_text_id")
    probes = probes.rename(columns={"probe_text_id": "unit_id"})
    keep = ["unit_id", "age", "age_band", "horizon_years", "horizon_band", "risk_class", "risk_level"]
    return pd.concat([inv[keep + ["objective_category", "experience_years", "investable_amount_cny",
                                  "income_stability"]], probes[keep]], ignore_index=True)


def code_call(rec: dict, menu: pd.DataFrame, menu_names: dict, attrs: dict):
    obj, status = extract_json(rec.get("content", ""))
    holdings = parse_portfolio(obj, menu_names) if obj is not None else []
    a = attrs[rec["unit_id"]]
    row = {k: rec[k] for k in ("call_id", "model_key", "condition", "sample", "unit_id", "replicate")}
    row.update({"model_returned": rec.get("model_returned"), "finish_reason": rec.get("finish_reason"),
                "run_id": rec.get("run_id"), "parse_status": status})
    usage = rec.get("usage") or {}
    row["prompt_tokens"] = usage.get("prompt_tokens")
    row["completion_tokens"] = usage.get("completion_tokens")
    row.update({k: a[k] for k in ("age", "age_band", "horizon_years", "horizon_band", "risk_class", "risk_level")})
    # secondary attributes (main sample only; NaN for probe texts) for covariate checks
    row.update({k: a.get(k, np.nan) for k in ("objective_category", "experience_years",
                                              "investable_amount_cny", "income_stability")})

    issues = []
    if status == "failed":
        issues.append("unparseable reply")
    hold = pd.DataFrame(holdings)
    if hold.empty:
        hold = pd.DataFrame(columns=["code", "code_source", "raw_code", "fund_name_given", "weight_raw"])
    hold["on_menu"] = hold["code"].isin(menu.index)
    # merge duplicate mentions of the same fund
    weight_sum = float(np.nansum(hold["weight_raw"])) if len(hold) else np.nan
    row["n_funds_listed"] = int(len(hold))
    row["n_funds"] = int(hold.loc[hold["on_menu"], "code"].nunique())
    row["weight_sum"] = weight_sum
    row["weight_sum_ok"] = bool(len(hold) and abs(weight_sum - 100) <= WEIGHT_TOL)
    row["n_missing_weights"] = int(hold["weight_raw"].isna().sum())
    row["off_menu_count"] = int((~hold["on_menu"]).sum())
    row["off_menu_weight"] = float(np.nansum(hold.loc[~hold["on_menu"], "weight_raw"]))
    row["fund_count_ok"] = 3 <= row["n_funds"] <= 8
    if row["off_menu_count"]:
        issues.append(f"off-menu codes: {', '.join(map(str, hold.loc[~hold['on_menu'], 'raw_code']))}")

    on = normalize_holdings(hold)
    row["portfolio_codable"] = bool(len(on))
    if len(on):
        f = menu.loc[on["code"]]
        w = on["w"].to_numpy()
        risk = f["risk_num"].to_numpy()
        row["equity_pct"] = float(np.sum(w * f["equity_exposure"].to_numpy()) / 100)
        row["weighted_risk"] = float(np.sum(w * risk) / 100)
        row["max_risk"] = float(np.max(risk))
        row["share_r4plus"] = float(w[risk >= 4].sum())
        for cls in ("Cash", "Bond", "Hybrid", "Equity", "Commodity"):
            row[f"share_{cls.lower()}"] = float(w[(f["asset_class"] == cls).to_numpy()].sum())
        row["share_qdii"] = float(w[(f["is_qdii"] == "1").to_numpy()].sum())
        row["hhi"] = float(np.sum((w / 100) ** 2))
        cap = next(r.max_product_risk for r in RISK_CLASSES if r.code == a["risk_class"])
        row["product_risk_cap"] = cap
        row["rating_breach"] = bool(row["max_risk"] > cap)
        row["rating_breach_weight"] = float(w[risk > cap].sum())
        row["equity_cap"] = suitable_equity_cap(a["risk_class"], a["horizon_band"])
        row["equity_cap_risk_only"] = EQUITY_CAP_BY_RISK[a["risk_class"]]
        row["excess_equity"] = max(0.0, row["equity_pct"] - row["equity_cap"])
        row["equity_over_cap"] = bool(row["equity_pct"] > row["equity_cap"] + EQUITY_TOL)
        row["holding_period_breach"] = bool((f["min_hold"].to_numpy() > a["horizon_years"]).any())
        row["equity_minus_100_age"] = row["equity_pct"] - max(0, 100 - a["age"])
        on_codes = sorted(on["code"])
    else:
        on_codes = []
    row["fund_set"] = ";".join(on_codes)

    if isinstance(obj, dict):
        warnings = obj.get("risk_warnings")
        row["n_risk_warnings"] = len(warnings) if isinstance(warnings, list) else np.nan
        dca = obj.get("dca_recommended")
        row["dca_recommended"] = dca if isinstance(dca, bool) else np.nan
        row["has_rebalancing_rule"] = bool(str(obj.get("rebalancing_rule", "")).strip())
        text = " ".join(str(obj.get(k, "")) for k in ("explanation", "suitability_check"))
        text += " " + " ".join(map(str, warnings)) if isinstance(warnings, list) else ""
        conflicts = obj.get("conflicts_identified")
        if isinstance(conflicts, list):
            text += " " + " ".join(map(str, conflicts))
            row["n_conflicts_listed"] = len([c for c in conflicts if str(c).strip()])
        else:
            row["n_conflicts_listed"] = np.nan
        row["mentions_conflict_terms"] = bool(CONFLICT_TERMS.search(text))
        row["mentions_horizon"] = bool(HORIZON_TERMS.search(text))
        rc = str(obj.get("risk_class_assessed", "")).upper()
        m = re.search(r"C([1-5])", rc)
        row["risk_class_assessed"] = f"C{m.group(1)}" if m else ""
        row["risk_class_assessed_diff"] = (int(m.group(1)) - int(a["risk_level"])) if m else np.nan
    # design-defined conflict: aggressive investor (C4/C5) with horizon under 3 years
    row["profile_risk_horizon_conflict"] = bool(a["risk_level"] >= 4 and a["horizon_band"] in ("H1", "H2"))

    hold_rows = hold.assign(call_id=rec["call_id"]).to_dict("records")
    return row, hold_rows, issues


def main(raw_dir: Path = RAW, menu_path: Path = ROOT / "data" / "fund_menu.csv",
         out: Path = ROOT / "outputs"):
    menu = load_menu(menu_path)
    menu_names = {name: code for code, name in menu["name_cn"].items()}
    attrs = unit_attributes().set_index("unit_id").to_dict("index")
    for k, v in attrs.items():
        v["unit_id"] = k
    rows, holdings, issues = [], [], []
    for path in sorted(raw_dir.glob("calls_*.jsonl")):
        seen = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if not rec.get("ok") or rec["call_id"] in seen:
                continue  # failed attempts are retried by the runner; keep the first success
            seen.add(rec["call_id"])
            row, hold, iss = code_call(rec, menu, menu_names, attrs)
            rows.append(row)
            holdings += hold
            issues += [{"call_id": rec["call_id"], "issue": i} for i in iss]
    if not rows:
        raise SystemExit("No successful calls found in outputs/raw; nothing to code.")
    pd.DataFrame(rows).to_csv(out / "experiment_results.csv", index=False)
    pd.DataFrame(holdings).to_csv(out / "experiment_holdings.csv", index=False)
    pd.DataFrame(issues, columns=["call_id", "issue"]).to_csv(out / "coding_issues.csv", index=False)
    print(f"Coded {len(rows)} replies; {len(issues)} issues logged.")


if __name__ == "__main__":
    main()
