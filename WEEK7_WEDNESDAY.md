# Week 7: Retrain and final demo (Wednesday: demo day)

<!-- PROVIDED -->

On Monday you closed the loop by hand: outcomes, challenger, gate, decision, promote or
keep. Now the system does it on its own, on Google Cloud, and you show it working.

```
Cloud Scheduler, every hour
   └─▶ drift-check (Cloud Run function): last hour of prediction logs vs. the reference
          └─ YOUR alerts fire? ─▶ drift_alert in the logs + start the retrain trigger
                                    └─▶ Cloud Build: data → retrain → compare → YOUR gate
                                         → YOUR decide → register models/vN/
                                         → promote? point the service at models/vN/
```

## 1. Your alerts

`config/alerts.yaml` holds your thresholds (null until you set them): the PSI that counts as
drift, how much more missing is too much, the PSI of the scores, and the fewest predictions
worth judging. Use what you proposed in your Week 6 monitoring report, and add the features
your batch 2 diagnosis found to `extra_features`. You also write `alerts` in
`functions/drift_check/drift.py`: which alerts fire for one window of predictions.

`python run.py reference` writes `reports/monitoring/drift_reference.json`: the training
data's bins and shares for your 20 most important features (SHAP, Week 6) plus your extra
features, and the scores'. **Summaries only, no applicant rows**: that is all the function
in the cloud needs, and it keeps the training data off it.

## 2. The function, the schedule, the pipeline

All of it is provided; you wire it together (`docs/cloud_shell_week7_wednesday.md`):

| Part | What it is | Runs as |
|---|---|---|
| `functions/drift_check/` | a Cloud Run function: reads the last hour of logs, computes PSI, calls your `alerts`, starts the retrain | its own service account: may read logs, the bucket, and start one trigger |
| Cloud Scheduler job | calls the function every hour (or now: `gcloud scheduler jobs run`) | the function's account |
| `cloudbuild_retrain.yaml` | the pipeline: data from the bucket, `src/cloud_retrain.py`, deploy only on "promote" | the build's account (Week 4) |
| `src/cloud_retrain.py` | Monday's retrain, comparison, YOUR gate and YOUR `decide`, then registers `models/vN/` | |

The pipeline registers every challenger it trains (a folder `models/vN/` with its bundle and
`decision.json`), and deploys it only if your rule says "promote". There is no MLflow server
in the cloud: the bucket's version folders are the registry.

Try the pipeline on your laptop first, with a folder standing in for the bucket:

```
mkdir -p /tmp/fakebucket/models/v1 && cp models/* /tmp/fakebucket/models/v1/
python run.py cloudretrain --bucket /tmp/fakebucket --champion /tmp/fakebucket/models/v1
```

## 3. The demo (about 8 minutes)

`docs/demo_checklist.md`: the live URL, drifted traffic (`python run.py send --batch 3
--drift-income 0.7`: incomes 30% lower, as in batch 2), the alert, the retrain it started,
the decision, and the promotion or a rollback drill. Rehearse it once with a timer.

## 4. The final submission

`docs/final_report.md`, `docs/runbook.md`, `docs/decision_record.md` (Monday),
`docs/automation.md`, your **completed** `docs/model_card.md` (Week 6's draft, finished: the
challenger, the decision, the monitoring loop), `docs/cost_note.md` (Billing → Reports), and
one `docs/reflections/<name>.md` per team member.

## Commands

```
python run.py test tests/test_week7_wed.py   # 7 tests (no data needed)
python run.py reference                      # reports/monitoring/drift_reference.json
python run.py cloudretrain --bucket DIR --champion DIR/models/v1   # the pipeline, locally
python run.py send --batch 3 --drift-income 0.7 --url https://...  # drifted traffic
python run.py evaluate                       # the zip added code under src/
python run.py check --stage wed              # the demo-day checks
python run.py check                          # the final submission
```

## The files today

| File | Status | What it is |
|---|---|---|
| `functions/drift_check/drift.py` | MIXED | **`alerts`** (yours); shares, PSI, window statistics (provided) |
| `functions/drift_check/main.py`, `requirements.txt` | PROVIDED | the function |
| `config/alerts.yaml` | **yours to fill** | your thresholds and extra features |
| `src/drift_reference.py` | PROVIDED | `python run.py reference` |
| `src/cloud_retrain.py`, `cloudbuild_retrain.yaml` | PROVIDED | the retrain pipeline |
| `scripts/send_batch.py` | PROVIDED (replaced) | adds `--drift-income` |
| `tests/test_week7_wed.py` | DO NOT EDIT | 7 tests |
| `scripts/check_week7.py` | DO NOT EDIT (replaced) | all Week 7 checks |
| `docs/cloud_shell_week7_wednesday.md` | PROVIDED | the wiring, step by step |
| `docs/demo_checklist.md` | PROVIDED | the 8 minutes |
| `docs/*_template.md` | PROVIDED | automation, runbook, final report, cost note, reflection |

## Rules this week

- Work on a branch, merge through pull requests; `python run.py evaluate` before you commit
  (config/alerts.yaml counts as code for the gate).
- The bucket stays private: `training/` holds Kaggle-derived data. Never commit `data/`,
  `models/`, or any key; the function and the build need none.
- Keep the service, the function and the schedule running until grades are out; then shut
  them down when the instructor says so, so nothing keeps costing credits.
