"""Verify the candidate fund menu against an external data source and write
the menu used in the experiment.

  python src/verify_funds.py --source fuyao       # course API (primary)
  python src/verify_funds.py --source eastmoney   # fallback
  python src/verify_funds.py --source csv         # manual ratings file

Input : data/fund_menu_candidates.csv  (identity already checked by web search)
Output: data/fund_menu.csv              final menu (menu_status = VERIFIED / NEEDS_REVIEW)
        data/fund_menu_verification.csv one row per fund with every retrieved field,
                                        source URL / raw file, and retrieval time

A fund is VERIFIED only if the retrieved name matches the candidate name and a
product risk rating (R1-R5) was retrieved. The experiment runner refuses to
start while any menu fund is not VERIFIED.

Equity exposure: for funds that hold stocks directly (bond, hybrid and
non-feeder equity funds) the latest reported stock share of net assets is
used; for ETF feeders, FOFs and the gold feeder the stated category
assumption (fallback_equity_pct) is used, because their reported allocation
shows fund units rather than the underlying exposure.
"""

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

from fund_data import get_source

ROOT = Path(__file__).resolve().parents[1]


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKC", str(name or ""))
    return re.sub(r"[\s()（）\-·]", "", s).upper()


def name_match(candidate: str, retrieved: str) -> str:
    if not retrieved:
        return "missing"
    if candidate == retrieved:
        return "exact"
    a, b = norm(candidate), norm(retrieved)
    if a == b:
        return "normalized"
    if a in b or b in a:
        return "partial"
    return "mismatch"


def reported_allowed(row) -> bool:
    t = row["official_type_cn"]
    feeder = "联接" in t or "联接" in row["name_cn"]  # 270042's type reads QDII/股票型 but it is an ETF feeder
    return row["asset_class"] in ("Bond", "Hybrid", "Equity") and "FOF" not in t and not feeder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="fuyao", choices=["fuyao", "eastmoney", "csv"])
    args = ap.parse_args()
    src = get_source(args.source)
    cand = pd.read_csv(ROOT / "data" / "fund_menu_candidates.csv", dtype=str).fillna("")
    records = []
    for _, row in cand.iterrows():
        info = src.basic_info(row["code"])
        info["candidate_name"] = row["name_cn"]
        info["name_match"] = name_match(row["name_cn"], info.get("name", ""))
        # Data providers show abbreviated display names (e.g. without "(QDII)" or "债券").
        # Such a fund is still the same product if manager and inception date both agree.
        mgr = norm(info.get("manager", ""))
        if (info["name_match"] == "mismatch" and mgr and norm(row["manager_cn"]).startswith(mgr)
                and str(info.get("inception", "")) == row["inception_date"]):
            info["name_match"] = "abbreviated (manager and inception match)"
        records.append(info)
        print(f"{row['code']} {row['name_cn']:<28} -> {info.get('name')} | {info.get('risk_rating')} | "
              f"{info['name_match']}")
    ver = pd.DataFrame(records)
    ver.to_csv(ROOT / "data" / "fund_menu_verification.csv", index=False)

    menu = cand.copy()
    by_code = ver.set_index("code")
    menu["risk_rating"] = menu["code"].map(by_code.get("risk_rating", pd.Series(dtype=str))).fillna("")
    menu["risk_rating_source"] = args.source
    if "retrieved_utc" in by_code:
        menu["risk_rating_retrieved"] = menu["code"].map(by_code["retrieved_utc"])
    if "reported_equity_pct" in by_code:
        menu["reported_equity_pct"] = menu["code"].map(by_code["reported_equity_pct"])
        menu["allocation_report_date"] = menu["code"].map(by_code.get("allocation_report_date"))
    rep = pd.to_numeric(menu.get("reported_equity_pct"), errors="coerce")
    use_rep = menu.apply(reported_allowed, axis=1) & rep.notna()
    menu["equity_exposure_pct"] = rep.where(use_rep, pd.to_numeric(menu["fallback_equity_pct"]))
    menu["equity_exposure_basis"] = use_rep.map({True: "reported stock share of net assets",
                                                 False: "category assumption"})
    ok = menu["code"].map(by_code["name_match"]).isin(["exact", "normalized", "partial",
                                                     "abbreviated (manager and inception match)"]) & (menu["risk_rating"] != "")
    menu["menu_status"] = ok.map({True: "VERIFIED", False: "NEEDS_REVIEW"})
    menu.to_csv(ROOT / "data" / "fund_menu.csv", index=False)
    print(f"\n{int(ok.sum())}/{len(menu)} funds VERIFIED. Risk ratings:\n"
          f"{menu['risk_rating'].value_counts().sort_index().to_string()}")
    if (~ok).any():
        print("Needs review:", ", ".join(menu.loc[~ok, "code"]))


if __name__ == "__main__":
    main()
