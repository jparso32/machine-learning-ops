# Real performance of the live model

Model version 1, threshold 0.085. Batches: the predictions the live service logged, joined with the true outcomes. Written by python run.py outcomes.

| Applicants | n | Default rate | Mean score | AUC | Cost per applicant | Approval rate | Bad rate among approved |
|---|---|---|---|---|---|---|---|
| validation (before going live) | 1000 | 8.1% | 0.081 | 0.736 | 0.564 | 72.9% | 4.7% |
| batch 1 (live) | 986 | 9.9% | 0.086 | 0.737 | 0.649 | 72.0% | 5.9% |
| batch 2 (live) | 1000 | 16.0% | 0.089 | 0.704 | 0.908 | 69.1% | 10.0% |

## What the monitoring said in Week 6 (before the outcomes)

| Batch | Approval rate | Mean score | Score PSI | Features with major drift |
|---|---|---|---|---|
| 1 | 72.0% | 0.086 | 0.009 | 0 |
| 2 | 69.1% | 0.089 | 0.012 | 4 |
