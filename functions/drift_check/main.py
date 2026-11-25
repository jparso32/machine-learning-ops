"""The drift check: a Cloud Run function that Cloud Scheduler calls every hour.

# PROVIDED: this whole file is finished. Your part is ``alerts`` in drift.py.

Each call:

1. reads the reference (bin edges and shares, and your thresholds) from your bucket:
   gs://BUCKET/monitoring/drift_reference.json (``python run.py reference`` writes it);
2. reads the prediction records your service logged in the last ``window_minutes`` from
   Cloud Logging (the same records as Week 6);
3. computes the PSI of every watched feature and of the scores, and the missing shares
   (drift.py), and asks YOUR ``alerts`` which alerts fire;
4. writes the result to gs://BUCKET/monitoring/last_check.json;
5. if an alert fires: writes a log entry ``{"event": "drift_alert", ...}`` with severity
   WARNING (the alert you show in the demo, in Logs Explorer), and starts the Cloud Build
   trigger that retrains, unless one was started less than ``cooldown_hours`` ago
   (gs://BUCKET/monitoring/state.json remembers when).

Settings come from environment variables, set when the function is deployed:
BUCKET (the bucket's name), TRIGGER_ID (the retrain trigger's id), SERVICE (credit-risk-api).
The project is the one the function runs in.

It answers with the result as JSON, so ``curl`` or Cloud Scheduler's log shows it.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from drift import alerts, check_thresholds, window_stats

REFERENCE = "monitoring/drift_reference.json"
LAST_CHECK = "monitoring/last_check.json"
STATE = "monitoring/state.json"


def _bucket():
    from google.cloud import storage

    return storage.Client().bucket(os.environ["BUCKET"])


def _read_json(name: str) -> dict[str, Any] | None:
    blob = _bucket().blob(name)
    return json.loads(blob.download_as_text()) if blob.exists() else None


def _write_json(name: str, value: dict[str, Any]) -> None:
    _bucket().blob(name).upload_from_string(json.dumps(value, indent=2),
                                            content_type="application/json")


def _project() -> str:
    import google.auth

    _, project = google.auth.default()
    return os.environ.get("PROJECT") or project


def recent_records(minutes: int, service: str, limit: int = 5000) -> list[dict[str, Any]]:
    """The prediction records of the last ``minutes`` minutes (newest first)."""
    from google.cloud import logging as cloud_logging

    since = (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat()
    query = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" '
             f'AND jsonPayload.event="prediction" AND timestamp>="{since}"')
    client = cloud_logging.Client(project=_project())
    records = []
    for entry in client.list_entries(filter_=query, order_by=cloud_logging.DESCENDING,
                                     max_results=limit, page_size=1000):
        if isinstance(entry.payload, dict) and isinstance(entry.payload.get("features"), dict):
            records.append(entry.payload)
    return records


def start_retrain(trigger_id: str) -> str:
    """Run the Cloud Build trigger; return the build's id."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    project = _project()
    url = f"https://cloudbuild.googleapis.com/v1/projects/{project}/triggers/{trigger_id}:run"
    response = AuthorizedSession(credentials).post(url, json={"branchName": "main"})
    response.raise_for_status()
    return response.json().get("metadata", {}).get("build", {}).get("id", "")


def check(request: Any = None) -> tuple[str, int, dict[str, str]]:
    """The HTTP entry point (deployed with --entry-point=check)."""
    now = datetime.now(UTC)
    reference = _read_json(REFERENCE)
    if reference is None:
        return _answer({"error": f"gs://{os.environ['BUCKET']}/{REFERENCE} not found"}, 500)
    thresholds = reference["thresholds"]
    check_thresholds(thresholds)
    records = recent_records(int(thresholds["window_minutes"]),
                             os.environ.get("SERVICE", "credit-risk-api"))
    stats = window_stats(reference, records) if records else {"requests": 0}
    fired = alerts(stats, thresholds) if records else []
    result: dict[str, Any] = {"checked_at": now.isoformat(timespec="seconds"),
                              "window_minutes": thresholds["window_minutes"],
                              "requests": stats["requests"], "alerts": fired,
                              "score_psi": stats.get("score_psi"),
                              "top_psi": sorted(((n, f["psi"]) for n, f in
                                                 stats.get("features", {}).items()),
                                                key=lambda t: -t[1])[:5],
                              "retrain": "not needed"}
    if fired:
        state = _read_json(STATE) or {}
        last = state.get("last_retrain")
        cooldown = timedelta(hours=float(thresholds["cooldown_hours"]))
        if last and now - datetime.fromisoformat(last) < cooldown:
            result["retrain"] = f"skipped: one started at {last} (cooldown)"
        else:
            build_id = start_retrain(os.environ["TRIGGER_ID"])
            _write_json(STATE, {"last_retrain": now.isoformat(timespec="seconds"),
                                "build_id": build_id})
            result["retrain"] = f"started build {build_id}"
        print(json.dumps({"event": "drift_alert", "severity": "WARNING", **result}),
              flush=True)
    _write_json(LAST_CHECK, result)
    return _answer(result, 200)


def _answer(body: dict[str, Any], status: int) -> tuple[str, int, dict[str, str]]:
    return json.dumps(body, indent=2), status, {"Content-Type": "application/json"}
