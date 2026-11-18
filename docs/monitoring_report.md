# Monitoring report (Week 6)

Team: Team 2 — Credit Risk

Part 4 carry-over: sections 1–4, prepared November 17, 2026. The numerical evidence is the team's committed `week6-drift` results at commit `87bc7c64dc9a23289c78b182c9c4423c6d7258b8`.

## 1. What we monitor, and where the data comes from

The API records the inputs and result of each successful `/predict` call after building the response and before returning it. `api/prediction_log.py` writes one JSON line to standard output. Cloud Run sends that output to Cloud Logging, where the structured fields appear under `jsonPayload`.

| Logged field | Why we keep it |
|---|---|
| `event`, `severity` | Identify prediction records (`prediction`) and their log level (`INFO`). |
| `request_id` | A new UUID for each request lets us trace individual calls and distinguish repeated requests. |
| `timestamp` | UTC time establishes when the decision happened and lets us compare time windows. |
| `model_version` | Identifies the model responsible for the decision; the analyzed records use version `1`. |
| `SK_ID_CURR` | Associates the decision with an applicant and the appropriate production batch. |
| `overrides` | Records any income, credit, or annuity amounts supplied by the caller. |
| `features` | All 164 feature values actually passed to the model after lookup, overrides, and ratio recomputation. These show what the live model saw. |
| `probability`, `decision`, `threshold` | Preserve the estimated default risk and the resulting decision. Our threshold is `0.085`: scores at or above it are rejected. |

Missing feature values become JSON `null`, rather than invalid JSON `NaN`. A logging exception is caught and written as a warning so it does not prevent the API from returning the prediction. That also means HTTP success alone does not prove that a corresponding prediction log was retained.

The monitoring summary identifies its source as `cloud_logging` and its input as `data/logs/predictions.json`. The documented Cloud Shell extraction is:

```bash
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="credit-risk-api" AND jsonPayload.event="prediction"' \
  --freshness=7d --limit=5000 --format=json > predictions.json
cloudshell download predictions.json
```

The downloaded file belongs under `data/logs/` and is not committed because it contains applicant-level features. The committed evidence contains aggregates only. The summary does not record the exact extraction time or the raw export count, so those cannot be verified from the saved results alone.

`load_logs` filters prediction records and keeps the latest record for each applicant/model-version pair. After this processing, the summary contains **1,987 records**: 986 for batch 1, 1,000 for batch 2, and one batch 3 test request. The single batch 3 record is excluded from drift comparison because it is below the 100-record minimum.

The analyzed batch 1 window is November 16, 2026, **23:57:49–23:58:28 UTC**; batch 2 is **23:58:38–23:58:57 UTC**. Together these correspond to approximately 6:57:49–6:58:57 PM Eastern on November 16. Both send receipts report **1,000 requests and 1,000 HTTP 200 responses**. Therefore 14 batch 1 predictions are absent from the analyzed export. The saved evidence does not establish whether this arose from log delivery, export completeness, filtering, or deduplication. We should reconcile the export before treating batch 1 as fully observed; the figures below use its actual denominator of 986.

Feature drift is measured against **4,000 training rows (`X_train`)**, the inputs from which the model learned. We keep this reference fixed so a changing production distribution does not redefine normal. Scores and approval rates are compared with the held-out validation set scored by the same registered model and threshold. This gives an output baseline without using production outcome labels.

## 2. Batch 1

| Measure | Validation baseline | Batch 1 |
|---|---:|---:|
| Analyzed production requests | — | 986 |
| Approval rate | 72.90% | 72.01% |
| Mean predicted default probability | 0.0809 | 0.0864 |
| Score PSI against validation | — | 0.0094 |
| Features with PSI ≥ 0.10 | — | 0 of 164 |
| Features with PSI ≥ 0.25 | — | 0 of 164 |
| Evidently columns flagged as drifted | — | 6 of 164 (3.7%) |

Approval is 0.89 percentage points below validation and the mean score is 0.0055 higher. The score PSI is small, and no feature reaches our moderate-drift threshold. The largest feature PSI is `ORGANIZATION_TYPE` at 0.0821. These aggregates suggest a broadly similar batch, subject to the incomplete batch 1 log coverage.

Some individual comparisons differ. In the CSV, four numeric columns have KS p-values below 0.05: `CC_DRAWINGS_MEAN`, `LIVINGAREA_MEDI`, `LIVINGAREA_MODE`, and `DAYS_LAST_PHONE_CHANGE`. Their PSI values are only 0.0134–0.0198 and their KS statistics are 0.0546–0.0931, so these are small distribution differences rather than large PSI shifts.

Evidently reports six drifted columns, but its HTML files are not included in the committed results; the saved summary contains only the count. We cannot identify its six columns or equate them with the four KS findings above. A few flags among 164 comparisons can arise from sampling variation: for illustration, 164 tests at a nominal 5% significance level would produce 8.2 false positives on average if every null hypothesis were true. This is not a claim about Evidently's actual detector settings or proof that its six flags are false positives. Their practical importance should be judged using effect sizes, related features, missingness, and persistence in later batches.

## 3. Batch 2: what changed?

Batch 2 has 1,000 analyzed requests. Four of the 164 features have major drift (PSI ≥ 0.25); none fall in the moderate range. All other feature PSI values are below 0.10. Missing shares below are percentages; numeric means exclude missing values.

| Feature | PSI | KS statistic | Missing (training → batch 2) | Mean (training → batch 2) | What changed |
|---|---:|---:|---:|---:|---|
| `AMT_INCOME_TOTAL` | 1.0969 | 0.37425 | 0.00% → 0.00% | 168,454.79 → 116,653.42 | Mean income is 30.75% lower, with a large distribution shift. |
| `EXT_SOURCE_3` | 0.53445 | 0.03557 | 19.95% → 53.50% | 0.51128 → 0.51008 | Missingness rises by 33.55 percentage points; the observed values remain similar. |
| `ANNUITY_INCOME_RATIO` | 0.47449 | 0.29017 | 0.025% → 0.00% | 0.18397 → 0.26340 | The mean annuity-to-income ratio rises by about 43.18%. |
| `CREDIT_INCOME_RATIO` | 0.26051 | 0.21000 | 0.00% → 0.00% | 4.0392 → 5.7698 | The mean credit-to-income ratio rises by about 42.85%. |

The income and ratio shifts are connected. Both ratios divide by income, so a reduction in the income field raises both even when the credit and annuity fields remain broadly stable. The pattern is consistent with an upstream income scaling or transformation change, or a change in the applicant population. A roughly 30% income reduction would raise otherwise unchanged ratios by about 43%, which closely matches the observed pattern. The aggregate comparison cannot prove a specific conversion error or distinguish it conclusively from a real population change. The first investigation should compare the incoming income field and its transformation with the source system.

The `EXT_SOURCE_3` pattern points to a separate data-availability problem, such as an external score feed or join failing for more applicants. Its nonmissing mean barely changes, and the KS p-value is 0.6679, but over half the batch has no value. This is a material input change even though a test of only the available values does not flag it. We should check source coverage, joins, and missing-value handling.

| Output measure | Validation | Batch 1 | Batch 2 |
|---|---:|---:|---:|
| Approval rate | 72.90% | 72.01% | 69.10% |
| Mean predicted default probability | 0.0809 | 0.0864 | 0.0889 |
| Score PSI against validation | — | 0.0094 | 0.0117 |

Batch 2 approval is 3.80 percentage points below validation and 2.91 points below batch 1. Its mean score is 0.0080 above validation and 0.0025 above batch 1. The score PSI remains small despite the four major input shifts. That is not sufficient reassurance: similar score distributions do not establish that predictions are accurate, calibrated, fair, or producing acceptable lending costs. We do not yet have repayment outcomes in the monitoring evidence. We would investigate the input changes rather than infer that the model has handled them safely or automatically change its threshold.

## 4. How we measured it

**PSI** compares the proportions of reference and production observations in fixed bins. Our numeric bins are defined by training-data deciles, with repeated boundaries collapsed and an additional bin for missing values. For categorical columns, training categories define the bins, with missing or unseen categories placed in the extra bin. For each bin we calculate `(actual − expected) × ln(actual / expected)` and add the terms. Shares are floored at `0.0001` to avoid division by zero. Equal shares give zero PSI; larger redistribution gives a larger value. Our operational thresholds are 0.10 for moderate drift and 0.25 for major drift. They are investigation rules, not guarantees of model harm.

**KS** measures the largest vertical gap between two cumulative distributions. A KS statistic of 0.37425 for income means the largest cumulative-share difference is about 37.4 percentage points at some income value. Its p-value assesses evidence against equal distributions, rather than the size or business importance of a change. Large samples can make small differences statistically significant; testing many columns also creates opportunities for false positives. We therefore read the statistic and PSI alongside the p-value and investigate connected changes.

Our KS calculation drops missing values. PSI retains a missing bin, and the CSV also reports missing shares directly. This distinction explains `EXT_SOURCE_3`: KS sees similar distributions among the remaining observed scores, while PSI captures the large loss of coverage. Dropping missing values from every comparison would hide that failure.

Our PSI and Evidently agree that batch 2 needs investigation: PSI identifies four major feature shifts, and Evidently flags 9 of 164 columns (5.5%), compared with six in batch 1. Their counts can differ because the custom PSI rule and Evidently use different decision procedures. The committed summary does not preserve Evidently's individual flags or detector settings, so the exact cause of each disagreement cannot be established from this checkout. The four major PSI changes and the missingness diagnosis above are directly supported by the committed CSVs; the local Evidently HTML should be retained for that additional review. Neither tool's aggregate count establishes that model performance has degraded or remained acceptable.

Evidence: [`summary.json`](../reports/monitoring/summary.json), [`drift_batch1.csv`](../reports/monitoring/drift_batch1.csv), [`drift_batch2.csv`](../reports/monitoring/drift_batch2.csv), [`sent_batch1.json`](../reports/sent_batch1.json), [`sent_batch2.json`](../reports/sent_batch2.json), [`monitoring.py`](../src/monitoring.py), and [`prediction_log.py`](../api/prediction_log.py).

## 5. Proposed alerts

Scheduled for the later Week 6 submission (sections 5–6 are due after the Part 4 carry-over).

## 6. Limitations

Scheduled for the later Week 6 submission. The limitations relevant to the current analysis are recorded in sections 1–4: incomplete batch 1 log coverage, unavailable Evidently column details, and no observed repayment outcomes.
