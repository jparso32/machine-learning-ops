"""The drift reference: what "normal" looks like, small enough to live in the cloud.

# PROVIDED: this whole module is finished.

Run it with ``python run.py reference``. The drift-check function in the cloud cannot read
your training data (it is on your laptop, and it should stay private). So this writes only
summaries of it, the same ones your Week 6 ``psi`` used:

- for each watched feature: the training data's bin edges (10 equal shares) and the share
  of training applicants in each bin, plus the share missing (categorical features: the
  share of each category);
- the same for the champion's scores on the validation set;
- your thresholds from config/alerts.yaml.

Watched features: your ``top_features`` most important features (Week 6 SHAP,
reports/explain/shap_global.csv) plus your ``extra_features``. It writes
reports/monitoring/drift_reference.json (commit it, and upload it to
gs://BUCKET/monitoring/: docs/cloud_shell_week7_wednesday.md).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
import yaml

from src.experiment import load_training_data, load_week3_config
from src.monitoring import bin_shares, quantile_edges

ALERTS = Path("config/alerts.yaml")
SHAP = Path("reports/explain/shap_global.csv")
MODELS = Path("models")
OUT = Path("reports/monitoring/drift_reference.json")


# PROVIDED
def watched_features(config: dict[str, Any], alerts: dict[str, Any],
                     features: list[str]) -> list[str]:
    root = config["root"]
    if not (root / SHAP).exists():
        raise SystemExit(f"{SHAP} not found: python run.py explain (Week 6)")
    ranked = pd.read_csv(root / SHAP)["feature"].tolist()
    extra = list(alerts.get("extra_features") or [])
    unknown = [f for f in extra if f not in features]
    if unknown:
        raise SystemExit(f"extra_features {unknown} are not model features: check the names")
    return list(dict.fromkeys(ranked[: int(alerts["top_features"])] + extra))


# PROVIDED
def feature_reference(column: pd.Series, categorical: bool) -> dict[str, Any]:
    if categorical:
        shares = column.astype("string").value_counts(normalize=True, dropna=True)
        categories = sorted(shares.index.astype(str))
        missing = float(column.isna().mean())
        values = [float(shares.get(c, 0.0)) * (1 - missing) for c in categories]
        return {"kind": "categorical", "categories": categories, "shares": values + [missing]}
    edges = quantile_edges(column)
    return {"kind": "numeric", "edges": [float(e) for e in edges],
            "shares": [float(s) for s in bin_shares(column, edges)]}


# PROVIDED
def build_reference(config: dict[str, Any]) -> dict[str, Any]:
    root = config["root"]
    alerts = yaml.safe_load((root / ALERTS).read_text())
    info = json.loads((root / MODELS / "model_info.json").read_text())
    data = load_training_data(config, info["features"])
    watched = watched_features(config, alerts, info["features"])
    reference = {name: feature_reference(data.X_train[name], name in data.categorical)
                 for name in watched}
    model = joblib.load(root / MODELS / "model.joblib")
    scores = pd.Series(model.predict_proba(data.X_valid[info["features"]])[:, 1])
    score_ref = feature_reference(scores, categorical=False)
    return {"model_version": info["version"], "reference_rows": len(data.X_train),
            "thresholds": {k: alerts.get(k) for k in (
                "psi_alert", "missing_increase", "score_psi_alert", "min_requests",
                "window_minutes", "cooldown_hours")},
            "features": reference, "score": score_ref}


# PROVIDED
def main() -> None:
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    config = load_week3_config()
    reference = build_reference(config)
    path = config["root"] / OUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reference, indent=2) + "\n")
    unset = [k for k, v in reference["thresholds"].items() if v is None]
    print(f"{len(reference['features'])} watched features: "
          f"{', '.join(list(reference['features'])[:8])}, ...")
    print(f"Wrote {OUT} ({path.stat().st_size / 1024:.0f} KB, summaries only).")
    if unset:
        print(f"WARNING: thresholds not set in config/alerts.yaml: {unset}. The function "
              "refuses to run until they are.")


if __name__ == "__main__":
    main()
