# Deployment (Week 5)

Team: 2

Status: deployed successfully on November 15, 2026. Revision
`credit-risk-api-00001-dbs` serves 100% of traffic. Live health and model metadata, private
bucket configuration, service access policies and prediction/error responses are verified.
The Wednesday and full Week 5 checkpoints passed. Cloud latency is recorded.

| Setting | Verified value or current status |
|---|---|
| Service URL | https://credit-risk-api-480708713552.us-central1.run.app |
| Alternate status URL | https://credit-risk-api-7b7so7xvaa-uc.a.run.app |
| Revision / traffic | `credit-risk-api-00001-dbs` / 100% |
| Project id / region | `credit-risk-team2` / `us-central1` |
| Image | `us-central1-docker.pkg.dev/credit-risk-team2/credit-risk/api:week5` |
| Pushed image digest | `sha256:455b2f345f5fdedd56d3133bcbfe420a75e22055118e00cf1f6b316844ce0a06` |
| Model bucket | `gs://credit-risk-models-team2`; public access prevention enforced; uniform bucket-level access true; no `allUsers` bucket binding |
| Model version | Live version `1`; threshold `0.085`; 164 features; data version `c393a114d6e3`; validation AUC `0.735588871424925` |
| Model export timestamp | `2026-11-13T19:03:41+00:00` |
| Instances | Minimum 0, maximum 2 |
| Memory / CPU | 1 GiB / 1 CPU; concurrency 10, independently verified from service configuration |
| Service account | `credit-risk-api@credit-risk-team2.iam.gserviceaccount.com`; bucket-scoped `roles/storage.objectViewer` binding verified |
| Public service access | Cloud Run IAM grants `roles/run.invoker` to `allUsers`; model bucket remains private |

The deployment uses `--min-instances=0`, which matches [Cloud Run's default](https://docs.cloud.google.com/run/docs/configuring/min-instances).

The deployment script's live `/health` response reported `status: ok`, `model_loaded: true`
and model version `1`. `/model-info` reported the model values above. Independent requests
to the canonical service URL also verified health and these prediction responses:

| Request | Observed response |
|---|---|
| Applicant `100021` | HTTP 200; probability `0.10431654676258995`; decision `reject`; threshold `0.085` |
| Applicant `100021`, income override `-1` | HTTP 422 |
| Unknown applicant `1` | HTTP 404 |

Use the canonical service URL for live checks and latency measurements.

The Cloud Shell Wednesday checkpoint passed all required checks: the Python 3.12 slim
image uses pinned packages and appuser; data, models and the environment are excluded from
the image; and the live service reports version 1 and rejects applicant 100021.

[PR #5](https://github.com/jparso32/machine-learning-ops/pull/5) has a passing required
`pr-checks (credit-risk-team2)` check. [Cloud Build 557c5754](https://console.cloud.google.com/cloud-build/builds/557c5754-39ef-4d54-bd22-e82e8f675fd5?project=credit-risk-team2)
completed in 2m15s: lint passed, 191 tests passed, 10 skipped, and the model quality gate
passed. Cloud latency is recorded in `reports/latency.json`. The full Week 5 checkpoint passed all ten required checks, including 22 API tests and live-service verification.

## Verified local model lineage

The source main commit at `429c09b4b615a985774b58fcc8bd47955be60d79` records a calibrated
histogram gradient boosting model with threshold 0.085 and validation AUC
0.735588871424925. Its original serialized artifact was unavailable locally. The same
specification, calibration, seed, fixed split and feature table were used to rebuild it in a
fresh local registry. Validation AUC, Brier score, mean predicted probability, expected cost
and rejection rate reproduce the recorded values exactly. `reports/final_model.json`
records both the original source run and the new local run under `artifact_rebuild`.

## Deployment and measurement

Deployed with `scripts/deploy_week5_cloudshell.sh`. The image uses the pinned API runtime
and reads its model from the private bucket through the dedicated service account. Bucket
public access prevention and uniform access were independently verified. No account key is
required or committed.

After the successful endpoint and Wednesday checks, the service was left without test
traffic from `2026-11-15T16:47:11Z` until `2026-11-15T17:07:11Z`. The measurement ran from
the client Mac. The first request took 172.3 ms; the following
100 requests had p50 73.79 ms, p95 89.72 ms,
maximum 100.11 ms and 0 HTTP errors. The actual results are in
`reports/latency.json`; `reports/latency_local.json` preserves the earlier local-only run.

## Deploying a new model

Register and verify the new model locally, then run `python run.py export`. Check that all
three bundle files agree on version, features, threshold and data fingerprint. Upload all
three together to the private bucket and redeploy a new Cloud Run revision so each instance
loads the same snapshot. Verify the live `/model-info` and a prediction against the local
bundle before calling the rollout complete. Repeat the live latency measurement and Week 5
checks, then update the deployment record. Keep the service available through the end of
the course as required.
