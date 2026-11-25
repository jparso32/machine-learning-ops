"""Week 7 Wednesday: the drift check's alerts, its arithmetic, and the retrain pipeline file.

# DO NOT EDIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "functions" / "drift_check"))

from drift import alerts, numeric_shares, window_stats  # noqa: E402

THRESHOLDS = {"psi_alert": 0.25, "missing_increase": 0.10, "score_psi_alert": 0.10,
              "min_requests": 200}


def _stats(requests: int = 1000, score_psi: float = 0.02, **features: tuple) -> dict:
    return {"requests": requests, "score_psi": score_psi,
            "features": {name: {"psi": psi, "missing_ref": ref, "missing_now": now}
                         for name, (psi, ref, now) in features.items()}}


# DO NOT EDIT
def test_no_alert_when_all_is_well() -> None:
    stats = _stats(EXT_SOURCE_2=(0.03, 0.0, 0.0), DAYS_BIRTH=(0.01, 0.0, 0.0))
    assert alerts(stats, THRESHOLDS) == []


# DO NOT EDIT
def test_too_few_requests_is_not_an_alert() -> None:
    stats = _stats(requests=50, score_psi=0.9, AMT_INCOME_TOTAL=(1.2, 0.0, 0.0))
    assert alerts(stats, THRESHOLDS) == [], "50 predictions are too few to judge"


# DO NOT EDIT
def test_psi_alerts_in_name_order() -> None:
    stats = _stats(EXT_SOURCE_2=(0.03, 0.0, 0.0), CREDIT_INCOME_RATIO=(0.26, 0.0, 0.0),
                   AMT_INCOME_TOTAL=(1.1, 0.0, 0.0))
    assert alerts(stats, THRESHOLDS) == ["AMT_INCOME_TOTAL: PSI 1.10",
                                         "CREDIT_INCOME_RATIO: PSI 0.26"]


# DO NOT EDIT
def test_missing_and_score_alerts() -> None:
    stats = _stats(score_psi=0.15, EXT_SOURCE_3=(0.53, 0.20, 0.54),
                   OWN_CAR_AGE=(0.01, 0.66, 0.70))
    assert alerts(stats, THRESHOLDS) == ["EXT_SOURCE_3: PSI 0.53",
                                         "EXT_SOURCE_3: missing 20% -> 54%",
                                         "scores: PSI 0.15"]


# DO NOT EDIT
def test_thresholds_are_inclusive() -> None:
    stats = _stats(score_psi=0.10, A=(0.25, 0.0, 0.10))
    assert alerts(stats, THRESHOLDS) == ["A: PSI 0.25", "A: missing 0% -> 10%",
                                         "scores: PSI 0.10"]


# DO NOT EDIT
def test_window_stats_catch_an_income_drop() -> None:
    edges = [100.0, 200.0, 300.0]
    reference = {"features": {"AMT_INCOME_TOTAL": {"kind": "numeric", "edges": edges,
                                                   "shares": [0.25, 0.25, 0.25, 0.25, 0.0]}},
                 "score": {"edges": [0.5], "shares": [0.5, 0.5, 0.0]}}
    normal = [{"features": {"AMT_INCOME_TOTAL": v}, "probability": p}
              for v, p in zip([50, 150, 250, 350] * 100, [0.2, 0.8] * 200, strict=True)]
    dropped = [{**r, "features": {"AMT_INCOME_TOTAL": r["features"]["AMT_INCOME_TOTAL"] * 0.4}}
               for r in normal]
    assert window_stats(reference, normal)["features"]["AMT_INCOME_TOTAL"]["psi"] < 0.01
    assert window_stats(reference, dropped)["features"]["AMT_INCOME_TOTAL"]["psi"] > 0.25
    assert list(numeric_shares([None, 150], edges)) == [0.0, 0.5, 0.0, 0.0, 0.5]


# DO NOT EDIT
def test_retrain_pipeline_file() -> None:
    pipeline = yaml.safe_load((ROOT / "cloudbuild_retrain.yaml").read_text())
    assert [s["id"] for s in pipeline["steps"]] == ["data", "retrain", "deploy"]
    assert "promote.txt" in pipeline["steps"][2]["args"][-1], "deploy only on promote"
