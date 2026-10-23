"""Unit tests for the performance metrics, fee parsing and inter-coder agreement."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from manual_coding import cohen_kappa  # noqa: E402
from performance import _days_range, perf_metrics  # noqa: E402


def test_perf_metrics_known_series():
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    r = pd.Series([0.01, -0.02] * 12, index=idx)
    rf = pd.Series(0.001, index=idx)
    m = perf_metrics(r, rf)
    growth = (1.01 * 0.98) ** 12
    assert m["cagr_pct"] == pytest.approx(100 * (growth ** 0.5 - 1))
    # peak after the first month (1.01), trough at the end of the series
    assert m["max_drawdown_pct"] == pytest.approx(100 * (growth / 1.01 - 1))
    ex = r - rf
    assert m["sharpe"] == pytest.approx(ex.mean() * 12 / (ex.std(ddof=1) * np.sqrt(12)))
    assert m["calmar"] == pytest.approx((m["cagr_pct"] / 100) / abs(m["max_drawdown_pct"] / 100))


def test_perf_metrics_no_drawdown_has_no_calmar():
    idx = pd.date_range("2020-01-31", periods=12, freq="ME")
    m = perf_metrics(pd.Series(0.002, index=idx), pd.Series(0.001, index=idx))
    assert m["max_drawdown_pct"] == 0 and np.isnan(m["calmar"])


def test_redemption_conditions():
    assert _days_range("7天以下") == (0, 7)
    assert _days_range("365天(包含)-730天") == (365, 730)
    assert _days_range("730天以上(包含)") == (730, np.inf)
    assert _days_range(None) == (0, np.inf)


def test_cohen_kappa():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]) == pytest.approx(0.0)
