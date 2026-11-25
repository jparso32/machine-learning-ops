"""The drift check's arithmetic: shares, PSI, and which alerts fire.

Plain Python and numpy only, so it runs inside the Cloud Run function AND in the tests on
your laptop and in CI. main.py (the function) reads the logs and the reference from the
cloud and calls these.

The reference (reports/monitoring/drift_reference.json, from ``python run.py reference``)
holds, for every watched feature, the training data's bin edges and the share of training
applicants in each bin (the last bin is "missing"): the same bins as your Week 6 ``psi``.
No applicant rows: only those shares.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

EPS = 1e-4  # as in Week 6: an empty bin would make the logarithm infinite


# PROVIDED
def numeric_shares(values: list[Any], edges: list[float]) -> np.ndarray:
    """Shares of ``values`` in the bins defined by ``edges``, plus a last bin for missing."""
    x = np.array([np.nan if v is None else float(v) for v in values], dtype=float)
    missing = np.isnan(x)
    counts = np.bincount(np.searchsorted(np.asarray(edges, dtype=float), x[~missing],
                                         side="right"), minlength=len(edges) + 1)
    return np.append(counts, missing.sum()) / max(len(x), 1)


# PROVIDED
def category_shares(values: list[Any], categories: list[str]) -> np.ndarray:
    """Shares of each training category, plus a last bin for missing or unseen ones."""
    index = {c: i for i, c in enumerate(categories)}
    counts = np.zeros(len(categories) + 1)
    for v in values:
        counts[index.get(None if v is None else str(v), len(categories))] += 1
    return counts / max(len(values), 1)


# PROVIDED
def psi_from_shares(expected: list[float] | np.ndarray, actual: np.ndarray) -> float:
    """PSI between the reference shares and the current shares (Week 6's formula)."""
    e = np.clip(np.asarray(expected, dtype=float), EPS, None)
    a = np.clip(np.asarray(actual, dtype=float), EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


# PROVIDED
def window_stats(reference: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """PSI and missing shares for every watched feature, and the PSI of the scores.

    ``records`` are prediction log records (Week 6: each has "features" and "probability").
    """
    features: dict[str, dict[str, float]] = {}
    for name, ref in reference["features"].items():
        values = [r["features"].get(name) for r in records]
        if ref["kind"] == "numeric":
            shares = numeric_shares(values, ref["edges"])
        else:
            shares = category_shares(values, ref["categories"])
        features[name] = {"psi": round(psi_from_shares(ref["shares"], shares), 4),
                          "missing_ref": round(float(ref["shares"][-1]), 4),
                          "missing_now": round(float(shares[-1]), 4)}
    scores = numeric_shares([r.get("probability") for r in records],
                            reference["score"]["edges"])
    return {"requests": len(records), "features": features,
            "score_psi": round(psi_from_shares(reference["score"]["shares"], scores), 4)}


# TODO(student)
def alerts(stats: dict[str, Any], thresholds: dict[str, Any]) -> list[str]:
    """Every alert that fires for this window; an empty list means all is well.

    Args:
        stats: from ``window_stats``: ``requests``, ``score_psi``, and ``features``:
            {name: {"psi", "missing_ref", "missing_now"}}.
        thresholds: config/alerts.yaml (psi_alert, missing_increase, score_psi_alert,
            min_requests).

    Returns:
        One sentence per alert, in this order:

        1. If ``requests`` is below ``min_requests``: return an EMPTY list (too few
           predictions to judge; that is not an alert).
        2. For each feature, in name order (``sorted``), whose PSI is at least
           ``psi_alert``: ``f"{name}: PSI {psi:.2f}"``.
        3. For each feature, in name order, whose missing share rose by at least
           ``missing_increase``: ``f"{name}: missing {ref:.0%} -> {now:.0%}"``.
        4. If ``score_psi`` is at least ``score_psi_alert``: ``f"scores: PSI {psi:.2f}"``.
    """
    if stats["requests"] < thresholds["min_requests"]:
        return []

    messages = []
    features = sorted(stats["features"].items())

    for name, feature in features:
        psi = feature["psi"]
        if psi >= thresholds["psi_alert"]:
            messages.append(f"{name}: PSI {psi:.2f}")

    missing_threshold = thresholds["missing_increase"]
    for name, feature in features:
        ref = feature["missing_ref"]
        now = feature["missing_now"]
        increase = now - ref
        if increase >= missing_threshold or math.isclose(increase, missing_threshold):
            messages.append(f"{name}: missing {ref:.0%} -> {now:.0%}")

    score_psi = stats["score_psi"]
    if score_psi >= thresholds["score_psi_alert"]:
        messages.append(f"scores: PSI {score_psi:.2f}")

    return messages


# PROVIDED
def check_thresholds(thresholds: dict[str, Any]) -> None:
    """Refuse to run with unset thresholds (config/alerts.yaml still has nulls)."""
    unset = [k for k in ("psi_alert", "missing_increase", "score_psi_alert", "min_requests")
             if thresholds.get(k) is None or (isinstance(thresholds[k], float)
                                              and math.isnan(thresholds[k]))]
    if unset:
        raise ValueError(f"alert thresholds not set in config/alerts.yaml: {unset}")
