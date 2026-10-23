"""Draw the manual-validation sample for the keyword-based text codes.

60 main-sample replies (seed 7): 30 from conflict profiles (C4-C5 with
horizon under 3 years) and 30 from the rest, spread across models and
conditions. Writes docs/manual_coding_sample.csv with the reply text and two
empty columns for independent human coders. The automated code is kept in a
separate column that coders should hide while coding.

Run after code_responses.py:  python src/sample_for_manual_coding.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    res = pd.read_csv(ROOT / "outputs" / "experiment_results.csv")
    res = res[(res["sample"] == "main") & (res["parse_status"] != "failed")]
    picks = []
    for flag, n in ((True, 30), (False, 30)):
        pool = res[res["profile_risk_horizon_conflict"] == flag]
        per_cell = max(1, n // pool.groupby(["model_key", "condition"]).ngroups)
        part = pool.groupby(["model_key", "condition"], group_keys=False).apply(
            lambda g: g.sample(min(len(g), per_cell), random_state=7))
        picks.append(part.head(n))
    sample = pd.concat(picks)
    replies = {}
    for path in (ROOT / "outputs" / "raw").glob("calls_*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("ok") and rec["call_id"] in set(sample["call_id"]) and rec["call_id"] not in replies:
                replies[rec["call_id"]] = rec["content"]
    sample["reply_text"] = sample["call_id"].map(replies)
    sample["coder_1"] = ""
    sample["coder_2"] = ""
    cols = ["call_id", "model_key", "condition", "risk_class", "horizon_band", "reply_text", "coder_1", "coder_2",
            "mentions_conflict_terms"]
    sample[cols].to_csv(ROOT / "docs" / "manual_coding_sample.csv", index=False)
    print(f"Wrote {len(sample)} replies to docs/manual_coding_sample.csv")


if __name__ == "__main__":
    main()
