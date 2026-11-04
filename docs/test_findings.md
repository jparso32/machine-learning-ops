<!-- PROVIDED: copy this file to docs/test_findings.md and fill in every placeholder.
     The check fails while the word in capitals below is still anywhere in the file. -->

# Test findings (Week 4)

Team: Rithvik, Jayden

Run `python run.py testreport` and copy the counts from `reports/test_report.md`.

| Kind | Tests | Passed | Failed | Known failures (xfail) | Skipped |
|---|---:|---:|---:|---:|---:|
| Unit | 5 | 5 | 0 | 0 | 0 |
| Data | 5 | 5 | 0 | 0 | 0 |
| Model | 4 | 2 | 2 | 0 | 0 |

## Limits we chose, and why

For each data test and model test, the limit you picked (for example "default rate
between 6% and 10%", "no score moves by more than 0.001") and why that number: what you saw
in the data, and what a change past the limit would mean.

| Test | Limit | Why This Limit Was Chosen | Meaning of Failure |
|---|---|---|---|
| `test_one_row_per_applicant` | Exactly one row per `SK_ID_CURR`. | Each applicant should have one feature row. | Duplicate rows could cause applicants to be counted multiple times and distort model training. |
| `test_schema` | Required columns must exist; `TARGET` must contain only 0 or 1; required numeric features must be numeric. | The model depends on the required columns, data types, and binary target labels. | Missing columns or invalid values could break the pipeline or produce unreliable predictions. |
| `test_value_ranges` | Ages between 18 and 70 years; income greater than 0; columns ending in `_RATE` or `_SHARE` between 0 and 1. | These limits check that important features contain plausible values. | Values outside these ranges could indicate corrupted data or incorrect feature calculations. |
| `test_missing_values` | Income, credit amount, `DAYS_BIRTH`, and `TARGET` cannot be missing; fewer than 1% of `EXT_SOURCE_2` values may be missing; no column can be entirely missing. | Required features and labels must be available. The 1% limit is the threshold specified in the test. | Missing values could indicate data-quality problems or an unexpected change in the feature pipeline. |
| `test_default_rate` | Default rate between 6% and 10%. | The expected default rate is approximately 8%, and this range allows some variation. | A rate outside the range could indicate incorrect labels, a changed sample, or a different applicant population. |

### Model Tests

| Test | Limit | Why This Limit Was Chosen | Result and Meaning |
|---|---|---|---|
| `test_minimum_auc` | Validation ROC-AUC at least 0.70. | The Week 1 logistic regression achieved an AUC of 0.710, so 0.70 is the minimum acceptable performance threshold. | **Passed.** The model met the minimum performance requirement. |
| `test_application_weekday_does_not_change_the_score` | Maximum score change of 0.001. | Application weekday should not influence credit risk. The tolerance allows negligible numerical variation. | **Passed.** Changing the application weekday did not change scores beyond the limit. |
| `test_gender_does_not_change_the_score` | Maximum score difference of 0.01 between otherwise identical applicants with gender set to `F` or `M`. | The project policy requires gender not to affect scores, while allowing a small tolerance for numerical differences. | **Failed.** The maximum difference was 0.102748, meaning changing only gender substantially affected some risk scores. |
| `test_higher_income_does_not_raise_risk` | No score may increase by more than 0.001 after income increases by 50% and dependent ratios are recomputed. | Higher income alone should not increase predicted default risk. The tolerance allows negligible numerical variation. | **Failed.** Twenty-four applicants became riskier, with a maximum score increase of 0.083670. |


## Findings

Write one section per test that failed. Name the test exactly as in the report (for example
`test_higher_income_does_not_raise_risk`). If no test failed, write "No test failed" and
say which test you expected to be the most likely to fail, and why.

### test_gender_does_not_change_the_score

- **What failed:** The test failed because changing `CODE_GENDER` from `F` to `M` changed predicted risk scores by up to **0.102748**, exceeding the allowed difference of 0.01.
- **Why:** The model's predictions depend on gender, either directly through `CODE_GENDER` or indirectly through learned relationships in the training data. The exact cause needs to be verified by inspecting the model's features and predictions for affected applicants.
- **Does it matter for the lender?** Yes. Applicants with otherwise identical characteristics could receive different risk scores based solely on gender, creating fairness and potential legal compliance concerns.
- **Decision:** Kept as a known failure pending investigation. The test should be marked with `@pytest.mark.xfail(strict=True, reason="see docs/test_findings.md")` only if the team explicitly accepts the failure temporarily. The model should be fixed and retested before deployment, for example by removing gender as a predictive feature and evaluating whether other features act as proxies.

### test_higher_income_does_not_raise_risk

- **What failed:** The test failed because **24 applicants** received higher risk scores after their income increased by 50%. The largest score increase was **0.083670**, exceeding the allowed increase of 0.001.
- **Why:** Increasing income also changes income-dependent ratio features through `change_income(X, 1.5)`. The model may assign risk-increasing effects to these ratios or their interactions with other features. The exact cause needs to be verified by examining the changed features and the predictions of the affected applicants.
- **Does it matter for the lender?** Yes. Applicants with higher incomes could be assigned greater predicted default risk despite all other underlying characteristics remaining unchanged, potentially leading to unfair or inconsistent lending decisions.
- **Decision:** Kept as a known failure pending investigation. The test should be marked with `@pytest.mark.xfail(strict=True, reason="see docs/test_findings.md")` only if the team explicitly accepts the failure temporarily. Inspect the affected predictions and income-dependent features, then consider retraining or applying a monotonic constraint so higher income cannot increase predicted risk. Retest the model before treating the issue as resolved.



## Decisions on Known Model Test Failures

### test_gender_does_not_change_the_score

- **Decision:** Kept as a known failure using `@pytest.mark.xfail(strict=True, reason="see docs/test_findings.md")`.
- **Reason:** Changing only gender caused a maximum score difference of 0.102748, exceeding the allowed 0.01. This indicates that gender affects the model's predictions. The issue is being documented rather than hiding it by changing the test.
- **Future action:** Investigate the influence of gender and potential proxy features. The model must be updated and the test must pass before this issue can be considered resolved.

### test_higher_income_does_not_raise_risk

- **Decision:** Kept as a known failure using `@pytest.mark.xfail(strict=True, reason="see docs/test_findings.md")`.
- **Reason:** Increasing income by 50% caused 24 applicants to receive higher risk scores. The largest increase was 0.083670, exceeding the allowed 0.001. This violates the expected relationship between income and predicted risk.
- **Future action:** Investigate income-related ratio features and their influence on predictions. Consider retraining with appropriate monotonic constraints and retest before considering the issue resolved.