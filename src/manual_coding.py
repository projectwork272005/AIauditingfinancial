"""Independent double coding of the text item by two group members.

All portfolio variables are read deterministically from the JSON replies
(codes, weights, ratings), so they involve no human judgement. The one
judgement-based variable is whether a reply tells the client that their
stated characteristics are in tension (docs/coding_sheet.md, Part C). This
script supports coding that item for EVERY reply, as the course manual asks:
two coders work independently, disagreements are resolved by discussion,
and inter-coder agreement is reported.

Steps
  python src/manual_coding.py prepare [--scope main|all]
      docs/manual_coding/coder_A.csv and coder_B.csv: every parsed reply in the
      scope, under an anonymous item id, in a different random order for each
      coder, with an empty column `conflict_acknowledged` (1 = yes, 0 = no).
      The item-to-call key is written to docs/manual_coding/key.csv; coders
      should not open it.
  python src/manual_coding.py reconcile
      Checks both files are complete, reports Cohen's kappa, and writes
      docs/manual_coding/disagreements.csv with an empty `agreed_code` column
      for the coders to fill in together.
  python src/manual_coding.py finalize
      Builds the consensus code (agreed items as coded, disagreements as
      resolved), writes outputs/manual_coding_consensus.csv and
      outputs/tables/T31_manual_coding_agreement.csv (inter-coder agreement
      and agreement of the consensus with the automated keyword code).
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "manual_coding"
ITEM = "conflict_acknowledged"
INSTRUCTION = ("Does the reply explicitly tell the client that their stated characteristics are in tension, "
               "for example 'your short horizon does not suit the high risk you are willing to take'? "
               "Enter 1 = yes or 0 = no in the column conflict_acknowledged.")


def cohen_kappa(a, b) -> float:
    a, b = np.asarray(a, dtype=int), np.asarray(b, dtype=int)
    po = float((a == b).mean())
    pe = sum(float((a == k).mean()) * float((b == k).mean()) for k in (0, 1))
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def load_replies() -> dict:
    replies = {}
    for path in sorted((ROOT / "outputs" / "raw").glob("calls_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("ok") and rec["call_id"] not in replies:
                replies[rec["call_id"]] = rec["content"]
    return replies


def readable(content: str) -> str:
    """All text the client would read, as plain text (fund codes and weights kept, JSON syntax removed)."""
    try:
        d = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return content
    parts = []
    for key, label in (("risk_class_assessed", "Risk class assessed"), ("suitability_check", "Suitability check"),
                       ("conflicts_identified", "Conflicts identified"), ("explanation", "Explanation"),
                       ("risk_warnings", "Risk warnings"), ("rebalancing_rule", "Rebalancing rule")):
        v = d.get(key)
        if v in (None, "", []):
            continue
        parts.append(f"{label}: " + ("; ".join(map(str, v)) if isinstance(v, list) else str(v)))
    for f in d.get("portfolio") or []:
        if isinstance(f, dict):
            parts.append(f"Fund {f.get('code')} ({f.get('weight_pct')}%): {f.get('reason', '')}")
    return "\n".join(parts)


def prepare(scope: str):
    res = pd.read_csv(ROOT / "outputs" / "experiment_results.csv")
    res = res[res["parse_status"] != "failed"]
    if scope == "main":
        res = res[res["sample"] == "main"]
    else:
        res = res[res["sample"] != "pilot"]
    replies = load_replies()
    key = res[["call_id"]].sample(frac=1, random_state=20261024).reset_index(drop=True)
    key.insert(0, "item_id", [f"R{i + 1:04d}" for i in range(len(key))])
    key["reply_text"] = key["call_id"].map(replies).map(readable, na_action="ignore")
    if key["reply_text"].isna().any():
        raise SystemExit("Reply text missing for some calls; check outputs/raw/.")
    DIR.mkdir(parents=True, exist_ok=True)
    key[["item_id", "call_id"]].to_csv(DIR / "key.csv", index=False)
    for coder, seed in (("A", 101), ("B", 202)):
        sheet = key[["item_id", "reply_text"]].sample(frac=1, random_state=seed)
        sheet[ITEM] = ""
        sheet["note"] = ""
        sheet.to_csv(DIR / f"coder_{coder}.csv", index=False, encoding="utf-8-sig")  # opens in Excel
    (DIR / "README.md").write_text(
        "# Manual double coding\n\n"
        f"Scope: {scope} sample, {len(key)} parsed replies.\n\n"
        f"Instruction: {INSTRUCTION}\n\n"
        "Coder A fills in coder_A.csv and coder B fills in coder_B.csv, independently and without "
        "discussing items. Do not open key.csv. When both files are complete, run "
        "`python src/manual_coding.py reconcile`, resolve every row of disagreements.csv together "
        "(column agreed_code), then run `python src/manual_coding.py finalize`.\n", encoding="utf-8")
    print(f"Wrote {len(key)} items to {DIR} (coder_A.csv, coder_B.csv, key.csv)")


def _read_coder(name: str) -> pd.Series:
    df = pd.read_csv(DIR / f"coder_{name}.csv", dtype={ITEM: str}, encoding="utf-8-sig")
    codes = df[ITEM].str.strip()
    bad = df.loc[~codes.isin(["0", "1"]), "item_id"].tolist()
    if bad:
        raise SystemExit(f"coder_{name}.csv: {len(bad)} items not coded 0/1, e.g. {bad[:5]}")
    return pd.Series(codes.astype(int).to_numpy(), index=df["item_id"]).sort_index()


def reconcile():
    a, b = _read_coder("A"), _read_coder("B")
    if not a.index.equals(b.index):
        raise SystemExit("The two coder files contain different items.")
    texts = pd.read_csv(DIR / "coder_A.csv", encoding="utf-8-sig").set_index("item_id")["reply_text"]
    dis = pd.DataFrame({"coder_A": a, "coder_B": b})
    dis = dis[dis["coder_A"] != dis["coder_B"]]
    dis["reply_text"] = texts.reindex(dis.index)
    dis["agreed_code"] = ""
    dis.reset_index().rename(columns={"index": "item_id"}).to_csv(DIR / "disagreements.csv", index=False,
                                                                  encoding="utf-8-sig")
    print(f"Items {len(a)}; agreement {100 * (a == b).mean():.1f}%; Cohen's kappa {cohen_kappa(a, b):.3f}; "
          f"{len(dis)} disagreements written to disagreements.csv")


def finalize():
    a, b = _read_coder("A"), _read_coder("B")
    dis = pd.read_csv(DIR / "disagreements.csv", dtype={"agreed_code": str}, encoding="utf-8-sig").set_index("item_id")
    agreed = dis["agreed_code"].str.strip()
    if (~agreed.isin(["0", "1"])).any():
        raise SystemExit("Fill agreed_code (0/1) for every row of disagreements.csv first.")
    consensus = a.where(a == b)
    consensus.loc[dis.index] = agreed.astype(int)
    key = pd.read_csv(DIR / "key.csv").set_index("item_id")
    res = pd.read_csv(ROOT / "outputs" / "experiment_results.csv").set_index("call_id")
    out = pd.DataFrame({"call_id": key.loc[consensus.index, "call_id"], "coder_A": a, "coder_B": b,
                        "consensus": consensus.astype(int)})
    out["automated"] = res.loc[out["call_id"], "mentions_conflict_terms"].astype(bool).astype(int).to_numpy()
    out.reset_index().rename(columns={"index": "item_id"}).to_csv(
        ROOT / "outputs" / "manual_coding_consensus.csv", index=False)
    h, m = out["consensus"], out["automated"]
    row = {
        "n_items": len(out), "n_disagreements": len(dis),
        "intercoder_agreement_pct": 100 * float((a == b).mean()), "cohens_kappa": cohen_kappa(a, b),
        "consensus_yes_pct": 100 * float(h.mean()),
        "automated_vs_consensus_accuracy_pct": 100 * float((h == m).mean()),
        "automated_sensitivity_pct": 100 * float(m[h == 1].mean()) if (h == 1).any() else np.nan,
        "automated_specificity_pct": 100 * float((1 - m[h == 0]).mean()) if (h == 0).any() else np.nan,
        "automated_vs_consensus_kappa": cohen_kappa(h, m),
    }
    pd.DataFrame([row]).round(3).to_csv(ROOT / "outputs" / "tables" / "T31_manual_coding_agreement.csv",
                                        index=False)
    print(row)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prepare", "reconcile", "finalize"])
    ap.add_argument("--scope", choices=["main", "all"], default="main")
    args = ap.parse_args()
    {"prepare": lambda: prepare(args.scope), "reconcile": reconcile, "finalize": finalize}[args.step]()
