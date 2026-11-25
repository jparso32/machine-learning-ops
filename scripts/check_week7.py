"""Week 7 checks. Prints a PASS/FAIL table and exits non-zero if a required check fails.

# DO NOT EDIT: the instructor uses this exact script at checkpoints.

Run it with ``python run.py check --stage mon`` or ``--stage wed`` (what that checkpoint
needs), or ``python run.py check`` (everything the final submission needs). It calls your
LIVE service at the URL in docs/deployment.md (Week 5).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from scripts.check_week2 import CheckFailed, count_commit_authors
from scripts.check_week5 import check_live
from src.experiment import load_week3_config
from src.utils import DEFAULT_CONFIG

RETRAIN = Path("reports/retrain")
REFERENCE = Path("reports/monitoring/drift_reference.json")
ALERTS = Path("config/alerts.yaml")
BUILD_URL = re.compile(r"https://console\.cloud\.google\.com/cloud-build/builds[^\s)|]*")
FUNCTION_URL = re.compile(r"https://drift-check[a-z0-9.-]*\.(run\.app|cloudfunctions\.net)")
WATCH = ("AMT_INCOME_TOTAL", "EXT_SOURCE_3")


# DO NOT EDIT
def _pytest(config: dict[str, Any], *paths: str) -> str:
    result = subprocess.run([sys.executable, "-m", "pytest", *paths, "-q", "-p",
                             "no:cacheprovider"], cwd=config["root"], capture_output=True,
                            text=True)
    last = (result.stdout.strip().splitlines() or ["no output"])[-1]
    if result.returncode != 0:
        raise CheckFailed(f"{' '.join(paths)}: {last}")
    return last.strip("= ")


# DO NOT EDIT
def _json(config: dict[str, Any], rel: Path, hint: str) -> dict[str, Any]:
    path = config["root"] / rel
    if not path.exists():
        raise CheckFailed(f"{rel} not found; {hint}")
    return json.loads(path.read_text())


# DO NOT EDIT
def check_mon_tests(config: dict[str, Any]) -> str:
    return _pytest(config, "tests/test_week7_mon.py")


# DO NOT EDIT
def check_outcomes(config: dict[str, Any]) -> str:
    record = _json(config, RETRAIN / "outcomes.json", "python run.py outcomes")
    if record.get("source") != "cloud_logging":
        raise CheckFailed("outcomes were not computed from the Cloud Logging download (Week 6)")
    batches = record["batches"]
    if not {"1", "2"} <= set(batches):
        raise CheckFailed(f"outcomes for batches {sorted(batches)}; batches 1 and 2 needed")
    costs = ", ".join(f"batch {b} {r['real']['cost']:.3f}" for b, r in batches.items())
    return f"cost per applicant: validation {record['validation']['cost']:.3f}, {costs}"


# DO NOT EDIT
def check_challenger(config: dict[str, Any]) -> str:
    record = _json(config, RETRAIN / "challenger.json", "python run.py retrain")
    version = str(record["registered"]["version"])
    try:
        from mlflow import MlflowClient

        from src.tracking import setup_mlflow

        setup_mlflow(config)
        name = config["week3"]["final"]["registry"]["name"]
        registered = MlflowClient().get_model_version(name, version)
    except Exception as err:  # noqa: BLE001  (no MLflow database, or no such version)
        raise CheckFailed(f"challenger version {version} is not in the MLflow registry "
                          f"({type(err).__name__})") from err
    return (f"version {version} ({registered.status}), trained on "
            f"{record['trained_on']['total']:,} applicants")


# DO NOT EDIT
def check_decision(config: dict[str, Any]) -> str:
    decision = _json(config, RETRAIN / "decision.json", "python run.py champion")
    if decision.get("decision") not in ("promote", "keep") or not decision.get("reasons"):
        raise CheckFailed("decision.json has no decision with reasons")
    if "model_tests" not in decision or "gate_failures" not in decision:
        raise CheckFailed("decision.json was not made with the gate: python run.py champion")
    gate = "gate passed" if not decision["gate_failures"] else \
        f"gate failed ({len(decision['gate_failures'])})"
    return f"{decision['decision'].upper()} (v{decision['challenger_version']} vs " \
           f"v{decision['champion_version']}), {gate}"


# DO NOT EDIT
def check_serving(config: dict[str, Any]) -> str:
    """The live service runs the champion that models/ was exported from."""
    return check_live(config)


# DO NOT EDIT
def _doc(config: dict[str, Any], rel: str, min_words: int, needed: tuple[str, ...]) -> str:
    path = config["root"] / rel
    if not path.exists():
        raise CheckFailed(f"{rel} not found; copy its template")
    text = path.read_text()
    if "TODO" in text:
        raise CheckFailed(f"{rel} still contains TODO")
    words = len(text.split())
    if words < min_words:
        raise CheckFailed(f"{rel}: {words} words; answer every question")
    absent = [n for n in needed if n.lower() not in text.lower()]
    if absent:
        raise CheckFailed(f"{rel} does not mention {absent}")
    return f"{words} words"


# DO NOT EDIT
def check_decision_record(config: dict[str, Any]) -> str:
    return _doc(config, "docs/decision_record.md", 350, ("gate", "recent", "validation",
                                                          "rollback"))


# DO NOT EDIT
def check_wed_tests(config: dict[str, Any]) -> str:
    return _pytest(config, "tests/test_week7_wed.py")


# DO NOT EDIT
def check_alerts(config: dict[str, Any]) -> str:
    alerts = yaml.safe_load((config["root"] / ALERTS).read_text()) or {}
    unset = [k for k in ("psi_alert", "missing_increase", "score_psi_alert", "min_requests")
             if alerts.get(k) is None]
    if unset:
        raise CheckFailed(f"config/alerts.yaml: {unset} not set")
    reference = _json(config, REFERENCE, "python run.py reference")
    if reference["thresholds"].get("psi_alert") != alerts["psi_alert"]:
        raise CheckFailed("drift_reference.json is older than config/alerts.yaml: "
                          "python run.py reference (and upload it again)")
    missing = [f for f in WATCH if f not in reference["features"]]
    if missing:
        raise CheckFailed(f"the drift check does not watch {missing}: what did batch 2 show "
                          "in Week 6? (extra_features in config/alerts.yaml)")
    return (f"{len(reference['features'])} watched features; PSI >= {alerts['psi_alert']}, "
            f"missing +{alerts['missing_increase']}, at least {alerts['min_requests']} requests")


# DO NOT EDIT
def check_pipeline_files(config: dict[str, Any]) -> str:
    root = config["root"]
    needed = ["cloudbuild_retrain.yaml", "functions/drift_check/main.py",
              "functions/drift_check/drift.py", "functions/drift_check/requirements.txt"]
    missing = [f for f in needed if not (root / f).exists()]
    if missing:
        raise CheckFailed(f"missing {missing}")
    return "cloudbuild_retrain.yaml and the drift-check function"


# DO NOT EDIT
def check_automation(config: dict[str, Any]) -> str:
    text = _doc(config, "docs/automation.md", 250, ("psi", "promote"))
    body = (config["root"] / "docs/automation.md").read_text()
    if not BUILD_URL.search(body):
        raise CheckFailed("docs/automation.md has no link to a finished retrain build")
    if not FUNCTION_URL.search(body):
        raise CheckFailed("docs/automation.md has no drift-check function URL")
    return f"{text}; build link and function URL present"


# DO NOT EDIT
def check_runbook(config: dict[str, Any]) -> str:
    return _doc(config, "docs/runbook.md", 400, ("rollback", "gcloud run services update",
                                                 "drift_alert", "p95"))


# DO NOT EDIT
def check_final_report(config: dict[str, Any]) -> str:
    return _doc(config, "docs/final_report.md", 1200, ("champion", "gate", "drift",
                                                       "fairness"))


# DO NOT EDIT
def check_model_card(config: dict[str, Any]) -> str:
    return _doc(config, "docs/model_card.md", 700, ("intended use", "limitations",
                                                    "fairness", "monitoring", "challenger"))


# DO NOT EDIT
def check_cost_note(config: dict[str, Any]) -> str:
    text = _doc(config, "docs/cost_note.md", 200, ("cloud run", "cloud build", "month"))
    if "$" not in (config["root"] / "docs/cost_note.md").read_text():
        raise CheckFailed("docs/cost_note.md has no dollar amounts")
    return text


# DO NOT EDIT
def check_reflections(config: dict[str, Any]) -> str:
    folder = config["root"] / "docs" / "reflections"
    files = sorted(folder.glob("*.md")) if folder.exists() else []
    if len(files) < 2:
        raise CheckFailed("docs/reflections/ needs one reflection per team member")
    short = [f.name for f in files if "TODO" in f.read_text() or len(f.read_text().split()) < 250]
    if short:
        raise CheckFailed(f"unfinished reflections: {short}")
    return f"{len(files)} reflections"


Check = tuple[str, Callable[[dict[str, Any]], str]]
MONDAY: list[Check] = [
    ("mon tests", check_mon_tests),
    ("outcomes", check_outcomes),
    ("challenger", check_challenger),
    ("decision", check_decision),
    ("live service", check_serving),
]
WEDNESDAY: list[Check] = [
    ("wed tests", check_wed_tests),
    ("alerts", check_alerts),
    ("pipeline files", check_pipeline_files),
    ("automation", check_automation),
    ("live service", check_serving),
]
SUBMISSION: list[Check] = MONDAY + [("decision record", check_decision_record)] + \
    WEDNESDAY[:-1] + [("runbook", check_runbook), ("final report", check_final_report),
                      ("model card", check_model_card), ("cost note", check_cost_note),
                      ("reflections", check_reflections)]
STAGES = {"mon": MONDAY, "wed": WEDNESDAY, "all": SUBMISSION}


# DO NOT EDIT
def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Week 7 checks.")
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="path to config.yaml")
    parser.add_argument("--stage", choices=list(STAGES), default="all",
                        help="mon / wed: that checkpoint only; all: the final submission")
    args = parser.parse_args()
    config = load_week3_config(args.config)
    os.chdir(config["root"])

    failed = 0
    print(f"{'check':<16}{'result':<7}details")
    print("-" * 90)
    for name, check in STAGES[args.stage]:
        try:
            status, detail = "PASS", check(config)
        except CheckFailed as err:
            status, detail = "FAIL", str(err)
            failed += 1
        except Exception as err:  # a crash is a failure too, with the reason shown
            status, detail = "FAIL", f"{type(err).__name__}: {err}"
            failed += 1
        print(f"{name:<16}{status:<7}{detail}")
    print(f"{'git authors':<16}{'INFO':<7}{count_commit_authors(config['root'])}")
    print("-" * 90)
    print("All required checks passed." if not failed else f"{failed} required check(s) failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
