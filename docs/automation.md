<!-- PROVIDED: copy this file to docs/automation.md and fill in every placeholder.
     The check reads the build link from here. -->

# The automated loop (Week 7)

Team:

| Part                                 | Value                                                                                                                                                                                                                                                            |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Drift-check function URL             | https://drift-check-7b7so7xvaa-uc.a.run.app                                                                                                                                                                                                                      |
| Function's service account and roles | `drift-check@credit-risk-team2.iam.gserviceaccount.com` has Logs Viewer and Cloud Build Editor on the project, Storage Object Admin on `credit-risk-models-team2`, Service Account User on `cloud-build-ci`, and Cloud Run Invoker on the `drift-check` service. |
| Schedule                             | drift-check, hourly (0 \* \* \* \*), us-central1                                                                                                                                                                                                                 |
| Retrain trigger                      | retrain, main, cloudbuild_retrain.yaml                                                                                                                                                                                                                           |
| A finished retrain build             | https://console.cloud.google.com/cloud-build/builds;region=global/64b6cf4e-f463-4ef7-8325-e6ed119e209c;step=2?project=credit-risk-team2                                                                                                                          |
| What that build decided              | the decision was keep; the champion keeps serving.                                                                                                                                                                                                               |
| The version serving now              | `v1`, threshold `0.085`, verified via `/model-info`                                                                                                                                                                                                              |

## Our alert thresholds, and why

We set feature PSI to 0.25, the cutoff we used for major drift in Week 6. A
feature alerts if its missing share rises by at least 10 percentage points
above training. This catches problems like EXT_SOURCE_3 in batch 2, where
missingness went from 19.95% to 53.50%. We also use 0.25 for score PSI, so
small shifts in the score distribution do not trigger a retrain on their own.
In our cloud rehearsal, score PSI was only 0.0133 while income PSI was 1.00
and annuity-to-income PSI was 0.37. Both input alerts fired.

The function looks at the last 60 minutes and requires at least 100 predictions
before evaluating alerts. That keeps a handful of requests from triggering a
build. The six-hour cooldown prevents repeated builds for the same shift. We
watch the top 20 SHAP features and explicitly include AMT_INCOME_TOTAL,
EXT_SOURCE_3, ANNUITY_INCOME_RATIO, and CREDIT_INCOME_RATIO because those
were the four features with major drift in Week 6 batch 2.

## The loop, end to end

The credit-risk API logs prediction records in Cloud Logging. Each hour, Cloud
Scheduler calls the private drift-check function using the drift-check service
account. The function reads the recent logs and the drift reference from the
bucket, calculates PSI and missingness, and writes monitoring/last_check.json.

When an alert fires outside the cooldown, the function starts the retrain
trigger and records the build ID in monitoring/state.json. Cloud Build runs
as cloud-build-ci, trains and evaluates a challenger, and saves the versioned
model bundle and decision.json. If the decision is to promote, the build
updates Cloud Run to load the new model folder. If it decides to keep, the
current model stays live. An operator can pause the drift-check Scheduler job
to stop future scheduled checks.

## What we would change for a real lender

1. Wait for repayment outcomes from the affected period before retraining, so
   we can measure whether the drift actually hurt model performance.
2. Require human approval before promotion and review performance by subgroup.
3. Send alerts and build results to the on-call team, and roll out approved
   models to a small share of traffic before switching everyone over.
