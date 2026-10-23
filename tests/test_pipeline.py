"""Unit tests for the pipeline. All inputs here are hand-made TEST FIXTURES used
only to check that the code computes what it is supposed to compute. They are
not model outputs and are never written to outputs/.

Run: python -m pytest -q tests
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import backtest  # noqa: E402
import code_responses as cr  # noqa: E402
import prompts  # noqa: E402
import run_experiment  # noqa: E402
import validate_profiles  # noqa: E402

# ---------------------------------------------------------------- fixtures --

FIXTURE_MENU = pd.DataFrame({
    "code": ["000001", "000002", "000003", "000004"],
    "name_cn": ["测试货币", "测试债券", "测试指数", "测试养老FOF"],
    "asset_class": ["Cash", "Bond", "Equity", "Hybrid"],
    "is_qdii": ["0", "0", "1", "0"],
    "risk_num": [1.0, 2.0, 4.0, 3.0],
    "equity_exposure": [0.0, 10.0, 95.0, 50.0],
    "min_hold": [0.0, 0.0, 0.0, 3.0],
}).set_index("code")
NAMES = {n: c for c, n in FIXTURE_MENU["name_cn"].items()}


def attrs(risk_class="C2", risk_level=2, horizon_band="H2", horizon_years=2.0, age=40):
    return {"U1": {"unit_id": "U1", "age": age, "age_band": "A3", "horizon_years": horizon_years,
                   "horizon_band": horizon_band, "risk_class": risk_class, "risk_level": risk_level}}


def record(content):
    return {"call_id": "m|BASE|main|U1|r1", "model_key": "m", "condition": "BASE", "sample": "main",
            "unit_id": "U1", "replicate": 1, "content": content, "usage": {}}


# ------------------------------------------------------------------ parsing --

def test_extract_json_variants():
    obj = {"portfolio": []}
    assert cr.extract_json(json.dumps(obj)) == (obj, "ok")
    assert cr.extract_json("```json\n" + json.dumps(obj) + "\n```")[1] == "fenced"
    assert cr.extract_json("Here you go: " + json.dumps(obj) + " Thanks")[1] == "extracted"
    assert cr.extract_json('{"portfolio": [1, 2,],}')[1] == "repaired"
    assert cr.extract_json("no json here") == (None, "failed")


def test_coding_metrics_and_breaches():
    reply = {"portfolio": [{"code": "000001", "weight_pct": 50}, {"code": "000003", "weight_pct": "30%"},
                           {"code": "000004", "weight_pct": 20}],
             "dca_recommended": True, "rebalancing_rule": "annual",
             "risk_warnings": ["a", "b"], "explanation": "Despite the short horizon, this conflict is handled."}
    row, hold, issues = cr.code_call(record(json.dumps(reply)), FIXTURE_MENU, NAMES, attrs())
    assert row["weight_sum_ok"] and row["n_funds"] == 3 and row["off_menu_count"] == 0
    assert row["equity_pct"] == pytest.approx(0.5 * 0 + 0.3 * 95 + 0.2 * 50)
    assert row["weighted_risk"] == pytest.approx(0.5 * 1 + 0.3 * 4 + 0.2 * 3)
    assert row["max_risk"] == 4 and row["rating_breach"]           # C2 may hold up to R2
    assert row["rating_breach_weight"] == pytest.approx(50)        # R4 30% + R3 20%
    assert row["holding_period_breach"]                            # 3-year FOF, 2-year horizon
    assert row["share_qdii"] == pytest.approx(30)
    assert row["equity_cap"] == 20 and row["equity_over_cap"]      # min(C2 20, H2 30)
    assert row["mentions_conflict_terms"] and row["n_risk_warnings"] == 2


def test_off_menu_and_renormalisation():
    reply = {"portfolio": [{"code": "000001", "weight_pct": 40}, {"code": "999999", "weight_pct": 20},
                           {"code": "000002", "weight_pct": 40}]}
    row, _, issues = cr.code_call(record(json.dumps(reply)), FIXTURE_MENU, NAMES, attrs())
    assert row["off_menu_count"] == 1 and row["off_menu_weight"] == 20
    assert row["share_cash"] == pytest.approx(50) and row["share_bond"] == pytest.approx(50)
    assert not row["rating_breach"] and issues


def test_unparseable_reply_is_flagged_not_filled():
    row, hold, issues = cr.code_call(record("I cannot help with that."), FIXTURE_MENU, NAMES, attrs())
    assert row["parse_status"] == "failed" and not row["portfolio_codable"]
    assert "equity_pct" not in row and issues


# ------------------------------------------------------------------ prompts --

def test_base_prompt_is_prefix_of_suit_and_no_class_codes_leak():
    menu = pd.read_csv(ROOT / "data" / "fund_menu_candidates.csv", dtype=str).fillna("")
    base = prompts.build_system_prompt("BASE", menu, "d", "s")
    suit = prompts.build_system_prompt("SUIT", menu, "d", "s")
    assert suit.startswith(base) and len(suit) > len(base)
    profiles = pd.read_csv(ROOT / "data" / "investor_profiles.csv")
    for text in profiles["profile_text"]:
        assert not any(f"C{i}" in text for i in range(1, 6))


# ------------------------------------------------------------------ samples --

def test_profile_validation_passes():
    assert validate_profiles.main() == 0


def test_task_plan_counts():
    cfg = run_experiment.load_config()
    models = run_experiment.active_models(cfg, None)
    tasks = run_experiment.plan_tasks(cfg, ["main", "consistency", "probe"], ["BASE", "SUIT"], models)
    per_model = 2 * (200 + 80 + 138)
    assert len(tasks) == per_model * len(models)
    assert len({t["call_id"] for t in tasks}) == len(tasks)


# ----------------------------------------------------------------- backtest --

def test_series_metrics_known_values():
    r = pd.Series([0.01] * 24, index=pd.date_range("2024-01-31", periods=24, freq="ME"))
    m = backtest.series_metrics(r)
    assert m["cagr_pct"] == pytest.approx(100 * (1.01 ** 12 - 1))
    assert m["vol_pct"] == pytest.approx(0, abs=1e-9) and m["max_drawdown_pct"] == 0
    r2 = pd.Series([0.0] * 6 + [-0.10, -0.10] + [0.0] * 10,
                   index=pd.date_range("2024-01-31", periods=18, freq="ME"))
    m2 = backtest.series_metrics(r2)
    assert m2["max_drawdown_pct"] == pytest.approx(-19.0)
    assert m2["worst_12m_pct"] == pytest.approx(-19.0)


def test_monthly_returns_month_end_alignment():
    days = pd.bdate_range("2023-12-01", "2024-03-31")
    s = pd.Series(np.linspace(1.0, 1.3, len(days)), index=days)
    mr = backtest.monthly_returns({"X": s}, "2024-01-01", "2024-03-31")
    assert list(mr.index.month) == [1, 2, 3] and mr["X"].notna().all()


def test_auto_window_starts_after_first_common_month_end():
    a = pd.Series(1.0, index=pd.bdate_range("2021-10-25", "2026-09-30"))
    b = pd.Series(1.0, index=pd.bdate_range("2019-01-01", "2026-09-30"))
    assert backtest.auto_start({"A": a, "B": b}, "2026-09-30") == "2021-11-01"
    c = pd.Series(1.0, index=pd.bdate_range("2015-01-01", "2026-09-30"))
    assert backtest.auto_start({"C": c}, "2026-09-30") == "2021-10-01"     # capped at 60 months
