"""Run the recommendation experiment against the configured LLM APIs.

Every API call is appended as one JSON line to outputs/raw/calls_<model>.jsonl
the moment it finishes. Logs are append-only: earlier runs are never
overwritten, and a rerun skips every call_id that already has a successful
record, so an interrupted run can simply be restarted.

Examples
--------
  python src/run_experiment.py --list-models                 # check model IDs per provider
  python src/run_experiment.py --dry-run                     # plan + token estimate, no API calls
  python src/run_experiment.py --samples pilot               # pilot (excluded from analysis)
  python src/run_experiment.py --samples main consistency probe
  python src/run_experiment.py --models deepseek --samples main --max-calls 50
"""

import argparse
import json
import platform
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import llm_client
from prompts import build_system_prompt, build_user_prompt, load_menu, sha256

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "outputs" / "raw"
PLACEHOLDER = "SET_AFTER_LISTING_MODELS"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_config() -> dict:
    return json.loads((ROOT / "config" / "experiment_config.json").read_text(encoding="utf-8"))


def active_models(cfg: dict, keys: list[str] | None) -> list[dict]:
    models = [m for m in cfg["models"] if m["enabled"]]
    if keys:
        models = [m for m in models if m["key"] in keys]
    seen = set()
    for m in models:
        if m["key"] in seen:
            raise SystemExit(f"two enabled configurations share key '{m['key']}'; enable only one route")
        seen.add(m["key"])
    return models


def plan_tasks(cfg: dict, samples: list[str], conditions: list[str], models: list[dict]) -> list[dict]:
    inv = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    probes = pd.read_csv(ROOT / "data" / "probe_profiles.csv").drop_duplicates("probe_text_id")
    rng = np.random.default_rng(cfg["random_seed"])
    units = []
    if "pilot" in samples:
        pilot_ids = rng.choice(inv["investor_id"], size=cfg["samples"]["pilot"]["n_profiles"], replace=False)
        for _, r in inv[inv["investor_id"].isin(pilot_ids)].iterrows():
            units.append(("pilot", r["investor_id"], 1, r["profile_text"]))
    if "main" in samples:
        for _, r in inv.iterrows():
            units.append(("main", r["investor_id"], 1, r["profile_text"]))
    if "consistency" in samples:
        n_extra = cfg["samples"]["consistency"]["extra_replicates"]
        for _, r in inv[inv["in_consistency_subsample"]].iterrows():
            for rep in range(2, 2 + n_extra):
                units.append(("consistency", r["investor_id"], rep, r["profile_text"]))
    if "probe" in samples:
        for _, r in probes.iterrows():
            units.append(("probe", r["probe_text_id"], 1, r["profile_text"]))
    tasks = []
    for m in models:
        for cond in conditions:
            for sample, unit_id, rep, text in units:
                tasks.append({"call_id": f"{m['key']}|{cond}|{sample}|{unit_id}|r{rep}",
                              "model_key": m["key"], "condition": cond, "sample": sample,
                              "unit_id": unit_id, "replicate": rep, "profile_text": text})
    order = rng.permutation(len(tasks))  # random order: conditions/models not confounded with time
    return [tasks[i] for i in order]


def completed_ids(model_key: str) -> set[str]:
    path = RAW / f"calls_{model_key}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("ok"):
                    done.add(rec["call_id"])
    return done


def estimate_tokens(text: str) -> float:
    """Rule of thumb from DeepSeek's documentation: ~0.3 token per English
    character, ~0.6 per Chinese character. Used for budgeting only."""
    zh = sum(1 for ch in text if "一" <= ch <= "鿿")
    return 0.6 * zh + 0.3 * (len(text) - zh)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--samples", nargs="*", default=["main", "consistency", "probe"],
                    choices=["pilot", "main", "consistency", "probe"])
    ap.add_argument("--conditions", nargs="*", default=None, choices=["BASE", "SUIT"])
    ap.add_argument("--max-calls", type=int, default=None, help="stop after this many new calls")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    models = active_models(cfg, args.models)
    if args.list_models:
        for m in models:
            try:
                ids = llm_client.list_models(m)
                print(f"[{m['key']}] {m['base_url']}: {len(ids)} models")
                for i in ids:
                    print("   ", i)
            except Exception as exc:  # report and continue with the next provider
                print(f"[{m['key']}] could not list models: {exc}")
        return 0

    conditions = args.conditions or cfg["conditions"]
    menu_path = ROOT / cfg["menu"]["path"]
    if args.dry_run and not menu_path.exists():
        menu_path = ROOT / "data" / "fund_menu_candidates.csv"  # planning only; never used for real calls
    menu = load_menu(menu_path, require_verified=not args.dry_run)
    systems = {c: build_system_prompt(c, menu, cfg["menu"]["as_of"] or "UNVERIFIED",
                                      cfg["menu"]["source"] or "UNVERIFIED") for c in conditions}
    tasks = plan_tasks(cfg, args.samples, conditions, models)
    pending = [t for t in tasks if t["call_id"] not in completed_ids(t["model_key"])]

    summary = pd.DataFrame(tasks).groupby(["model_key", "sample", "condition"]).size()
    print("Planned calls (model, sample, condition):")
    print(summary.to_string())
    print(f"Total planned {len(tasks)}; already completed {len(tasks) - len(pending)}; pending {len(pending)}")
    in_tok = sum(estimate_tokens(systems[t["condition"]]) + estimate_tokens(build_user_prompt(t["profile_text"]))
                 for t in pending)
    print(f"Estimated input tokens for pending calls: {in_tok / 1e6:.2f} M "
          f"(output typically 400-1,200 tokens per call)")
    if args.dry_run:
        return 0

    for m in models:
        if m["model"] == PLACEHOLDER:
            raise SystemExit(f"model ID for '{m['key']}' not set; run --list-models and edit the config")
        if not llm_client.api_key_for(m):
            print(f"[{m['key']}] none of {llm_client.key_env_names(m)} is set: sending without a key header "
                  "(works only if the network proxy injects the key)")
    if args.max_calls is not None:
        pending = pending[: args.max_calls]

    RAW.mkdir(parents=True, exist_ok=True)
    prompt_dir = RAW / "prompts"
    prompt_dir.mkdir(exist_ok=True)
    for c, text in systems.items():
        p = prompt_dir / f"system_{c}_{sha256(text)[:12]}.txt"
        if not p.exists():
            p.write_text(text, encoding="utf-8")

    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    manifest = {"run_id": run_id, "started": now(), "args": vars(args), "python": sys.version,
                "platform": platform.platform(), "n_pending": len(pending),
                "system_prompt_sha256": {c: sha256(t) for c, t in systems.items()},
                "models": models}  # config holds only env-variable names, never keys
    (ROOT / "outputs" / "logs").mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "outputs" / "logs" / f"{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    by_key = {m["key"]: m for m in models}
    locks = {m["key"]: threading.Lock() for m in models}
    counts = {"ok": 0, "failed": 0}

    def work(task):
        m = by_key[task["model_key"]]
        system = systems[task["condition"]]
        user = build_user_prompt(task["profile_text"])
        started = now()
        res = llm_client.chat(m, cfg["generation"], system, user)
        rec = {k: v for k, v in task.items() if k != "profile_text"}
        rec.update({"run_id": run_id, "started_utc": started, "finished_utc": now(),
                    "provider_route": m["route"], "base_url": m["base_url"], "model_requested": m["model"],
                    "system_prompt_sha256": sha256(system), "user_prompt": user,
                    "user_prompt_sha256": sha256(user)})
        rec.update(res)
        with locks[m["key"]]:
            with open(RAW / f"calls_{m['key']}.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    t0 = time.time()
    pools = {m["key"]: ThreadPoolExecutor(max_workers=m["concurrency"]) for m in models}
    futures = [pools[t["model_key"]].submit(work, t) for t in pending]
    for i, fut in enumerate(as_completed(futures), 1):
        rec = fut.result()
        counts["ok" if rec["ok"] else "failed"] += 1
        if not rec["ok"]:
            print(f"[failed] {rec['call_id']}: {rec['error']}")
        if i % 25 == 0 or i == len(futures):
            rate = i / max(time.time() - t0, 1e-6)
            print(f"{i}/{len(futures)} done ({counts['failed']} failed), {rate:.2f} calls/s")
    for p in pools.values():
        p.shutdown()
    manifest.update({"finished": now(), "ok": counts["ok"], "failed": counts["failed"]})
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Finished: {counts['ok']} ok, {counts['failed']} failed. Rerun to retry failures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
