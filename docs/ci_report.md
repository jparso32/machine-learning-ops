<!-- PROVIDED: copy this file to docs/ci_report.md and fill in every placeholder.
     The check fails while the word in capitals below is still anywhere in the file. -->

# CI and the quality gate (Week 4)

Team: 2

## The pipeline

Cloud Build project: credit-risk-team2 (project id). Trigger: pr-checks (trigger name), on pull requests to
`main`. Branch protection on `main` requires the check: pr-checks (credit-risk-team2) (the check's name as GitHub
shows it).

| Step    | What it runs                                        | Why it is there                                                                                                                                                                                                            |
| ------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| install | `pip install -r requirements.txt`                   | the same packages as on our laptops                                                                                                                                                                                        |
| lint    | /workspace/.venv/bin/python -m ruff check .         | Catches lint errors before running the tests.                                                                                                                                                                              |
| test    | /workspace/.venv/bin/python -m pytest               | Runs the unit, data, and model tests using pytest’s default discovery. The two known model behavior failures are marked xfail and documented in docs/test_findings.md. (which tests run in CI, which are skipped, and why) |
| gate    | /workspace/.venv/bin/python -m scripts.quality_gate | there Rejects stale metrics and checks validation AUC, expected cost, AUC drop, and model-test failures against the configured thresholds.                                                                                 |

## Gate thresholds, and why

For each threshold in `config/gate.yaml`: the value, the number it is compared with today,
and why this value (what you looked at, and what passing or failing it would mean).

- **min_auc** = 0.70.\*\* The candidate's validation ROC-AUC was
  `0.7356`, above the `0.70` floor. This sets a minimum for how well
  the model ranks applicants by default risk.
- **max_cost** = 0.70.\*\* The candidate's expected cost was `0.564`
  per applicant at the decision threshold of `0.085`. The `0.70` cap
  leaves room for some variation while still requiring a lower cost
  than approving everyone (`0.810`) or rejecting everyone (`0.919`).
- **max_auc_drop** = 0.02.\*\* The candidate and registered model
  both had a validation ROC-AUC of about `0.736`. The gate allows a
  drop of at most `0.02` AUC points from the registered model so a
  candidate cannot pass with a large regression just by clearing `0.70`.
- **allow_failing_model_tests** = 0.\*\* The evaluation recorded
  `2` passes, `0` failures, and `2` documented expected failures.
  The gate allows zero unexpected model-test failures.

## Evidence

- A green Cloud Build run on a pull request: https://console.cloud.google.com/cloud-build/builds/67797170-02f5-46dc-ac66-75d96da4d62e?project=credit-risk-team2 (paste the link to the build page:  
  starts with https://console.cloud.google.com/cloud-build/)
- A red run, and what made it red: https://console.cloud.google.com/cloud-build/builds/95b5d515-50be-4312-9a43-1de848933f3f?project=credit-risk-team2 (the link, and the gate's message)
- How the red pull request was handled: GitHub blocked the merge because `pr-checks` is required on `main`. We closed the demo PR without merging it.
