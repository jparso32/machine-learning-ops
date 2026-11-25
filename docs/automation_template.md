<!-- PROVIDED: copy this file to docs/automation.md and fill in every placeholder.
     The check reads the build link from here. -->

# The automated loop (Week 7)

Team: TODO

| Part | Value |
|---|---|
| Drift-check function URL | TODO (https://drift-check-....run.app) |
| Function's service account and roles | TODO (drift-check@...: Logs Viewer, Cloud Build Editor, Storage Object Admin on the bucket, Service Account User on the build account) |
| Schedule | TODO (Cloud Scheduler job drift-check, "0 * * * *") |
| Retrain trigger | TODO (name retrain, id ..., cloudbuild_retrain.yaml, service account ...) |
| A finished retrain build | TODO (https://console.cloud.google.com/cloud-build/builds/...) |
| What that build decided | TODO (version N registered; promoted / kept, and why) |
| The version serving now | TODO (from /model-info) |

## Our alert thresholds, and why

TODO: Each value in config/alerts.yaml (psi_alert, missing_increase, score_psi_alert,
min_requests, window_minutes, cooldown_hours, the extra features) with its reason: what it
catches, and what false alarms it avoids. Use your Week 6 numbers.

## The loop, end to end

TODO: What happens, step by step, from drifted traffic to the service loading a new model
(or keeping the old one): which component does what, under which identity, and what each
writes (logs, bucket files, versions). Where a person can stop it, and how.

## What we would change for a real lender

TODO: At least three things (for example: retrain only when the OUTCOMES of the drifted
period are known; a person approves every promotion; alerts by email or chat; a canary).
