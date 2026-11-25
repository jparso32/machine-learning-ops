"""The retrain pipeline that Cloud Build runs when the drift check raises an alert.

# PROVIDED: this whole module is finished. It reuses YOUR code: the recipe and the
# comparison from Monday, your quality gate (Week 4), and your ``decide``.

cloudbuild_retrain.yaml runs it after copying the training data from your bucket into
data/ (Cloud Build has no data of its own). It:

1. loads the champion: the bundle the live service runs now (``--champion``, the folder in
   its MODEL_BUCKET), so it compares against what is really serving;
2. trains a challenger with the champion's recipe on the training + labeled production
   applicants (``build_challenger``, as on Monday);
3. compares both on the fixed slices, runs the model tests and YOUR gate, calls YOUR
   ``decide`` (as ``python run.py champion`` does);
4. registers the challenger: its bundle goes into the next free folder ``models/vN/`` of
   the bucket, with decision.json next to it, WHATEVER the decision (a registered model is
   not a serving one);
5. if the decision is "promote", writes the new folder into ``--out``/promote.txt, and the
   next Cloud Build step points the service at it. If it is "keep", nothing is deployed.

There is no MLflow server in the cloud: here the bucket's version folders are the registry.

Run it on your laptop to try it (``python run.py cloudretrain --bucket /some/folder
--champion /some/folder/models/v1``): a local folder stands in for the bucket.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib

from src.champion import compare, decide, gate_challenger, model_tests_on
from src.export_model import _data_version, build_feature_store
from src.retrain import CHALLENGER, champion_record, load_retrain_config, retrain_data

BUNDLE = ("model.joblib", "model_info.json", "feature_store.parquet")


# PROVIDED
def is_gcs(uri: str) -> bool:
    return uri.startswith("gs://")


# PROVIDED
def fetch_bundle(source: str, target: Path) -> Path:
    """Copy a bundle folder (gs://bucket/models/vN or a local folder) into ``target``."""
    target.mkdir(parents=True, exist_ok=True)
    if is_gcs(source):
        from api.bundle import download_bundle

        return download_bundle(source, target)
    for name in BUNDLE:
        shutil.copy(Path(source) / name, target / name)
    return target


# PROVIDED
def existing_versions(bucket: str) -> list[int]:
    """The N of every models/vN/ folder in the bucket."""
    if is_gcs(bucket):
        from google.cloud import storage

        name = bucket.removeprefix("gs://").split("/")[0]
        paths = [b.name for b in storage.Client().list_blobs(name, prefix="models/")]
    else:
        root = Path(bucket) / "models"
        paths = [f"models/{p.name}/" for p in root.iterdir()] if root.exists() else []
    return sorted({int(m.group(1)) for p in paths if (m := re.match(r"models/v(\d+)/", p))})


# PROVIDED
def upload_folder(local: Path, bucket: str, prefix: str) -> str:
    """Copy every file of ``local`` to ``bucket``/``prefix``/; return that folder's URI."""
    if is_gcs(bucket):
        from google.cloud import storage

        name = bucket.removeprefix("gs://").split("/")[0]
        client_bucket = storage.Client().bucket(name)
        for path in local.iterdir():
            client_bucket.blob(f"{prefix}/{path.name}").upload_from_filename(str(path))
        return f"gs://{name}/{prefix}"
    target = Path(bucket) / prefix
    target.mkdir(parents=True, exist_ok=True)
    for path in local.iterdir():
        shutil.copy(path, target / path.name)
    return str(target)


# PROVIDED
def next_version(config: dict[str, Any], bucket: str, champion_version: str) -> int:
    """One above every version we know of: the bucket's folders, the champion, and
    Monday's challenger (so a version number never means two models)."""
    known = existing_versions(bucket) + [int(champion_version)]
    path = config["root"] / CHALLENGER
    if path.exists():
        known.append(int(json.loads(path.read_text())["registered"]["version"]))
    return max(known) + 1


# PROVIDED
def run_pipeline(bucket: str, champion_uri: str, out: Path) -> dict[str, Any]:
    config = load_retrain_config()
    root = config["root"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "promote.txt").unlink(missing_ok=True)

    serving = fetch_bundle(champion_uri, out / "champion")
    served_info = json.loads((serving / "model_info.json").read_text())
    recipe = champion_record(config)
    champion = {**recipe, "threshold": float(served_info["threshold"]),
                "features": served_info["features"],
                "registered": {"version": served_info["version"]}}
    champ_model = joblib.load(serving / "model.joblib")
    print(f"Champion: version {served_info['version']} from {champion_uri}")

    rd = retrain_data(config, champion["features"])
    print(f"Training the challenger on {len(rd.X):,} applicants ...")
    from src.retrain import build_challenger

    model, record = build_challenger(config, champion, rd)
    version = next_version(config, bucket, served_info["version"])
    bundle = out / f"v{version}"
    bundle.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, bundle / "model.joblib")
    record["registered"] = {"version": str(version)}
    record["model_path"] = str(bundle / "model.joblib")
    record_path = out / "challenger_record.json"
    record_path.write_text(json.dumps(record, indent=2, default=float) + "\n")

    comparison = compare(config, champion, record, champ_model, model)
    tests = model_tests_on(record_path, root)
    failures = gate_challenger(config, comparison, tests)
    verdict = decide(comparison, failures, config["retrain"]["decision"])

    store = build_feature_store(config, champion["features"])
    store.to_parquet(bundle / "feature_store.parquet", index=False)
    folder = f"models/v{version}"
    target = (f"gs://{bucket.removeprefix('gs://').split('/')[0]}/{folder}" if is_gcs(bucket)
              else str(Path(bucket) / folder))
    info = {
        "name": served_info.get("name", "credit-risk"), "version": str(version),
        "uri": target, "threshold": float(record["threshold"]),
        "features": champion["features"], "n_features": len(champion["features"]),
        "valid_auc": float(record["valid"]["valid_auc"]),
        "data_version": _data_version(config),
        "exported": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(), "n_applicants": len(store),
        "trained_on": record["trained_on"], "registered_by": "cloud retrain pipeline",
    }
    (bundle / "model_info.json").write_text(json.dumps(info, indent=2) + "\n")
    decision = {**verdict, "gate_failures": failures, "model_tests": tests,
                "champion_version": str(served_info["version"]),
                "challenger_version": str(version), "comparison": comparison,
                "created": info["exported"]}
    (bundle / "decision.json").write_text(json.dumps(decision, indent=2, default=float) + "\n")
    registered = upload_folder(bundle, bucket, folder)
    print(f"Registered version {version}: {registered}")
    if verdict["decision"] == "promote":
        (out / "promote.txt").write_text(registered)
    return {"version": version, "folder": registered, **verdict, "gate_failures": failures}


# PROVIDED
def main() -> None:
    parser = argparse.ArgumentParser(description="The automated retrain pipeline.")
    parser.add_argument("--bucket", required=True,
                        help="gs://BUCKET, or a local folder standing in for it")
    parser.add_argument("--champion", required=True,
                        help="the folder the service loads (its MODEL_BUCKET)")
    parser.add_argument("--out", default="data/cloudretrain",
                        help="working folder (Cloud Build: /workspace/out)")
    args = parser.parse_args()
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    result = run_pipeline(args.bucket, args.champion, Path(args.out))
    print(f"\nDecision: {result['decision'].upper()}")
    for reason in result["reasons"]:
        print(f"  - {reason}")
    if result["decision"] == "promote":
        print(f"The next step points the service at {result['folder']}.")
    else:
        print("Nothing is deployed: the champion keeps serving.")


if __name__ == "__main__":
    main()
