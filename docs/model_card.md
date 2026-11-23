<!-- PROVIDED: copy this file to docs/model_card.md and fill in every placeholder.
     A draft is due this week; Week 7 finishes it. Keep it short and factual: a reader who
     has never seen the project should understand what the model is for and when not to
     trust it. -->

# Model card: credit-risk (draft)

Team: 2 · Last updated: 11/22

## Model details

| | |
|---|---|
| Registered model | `credit-risk`, version 1, alias `staging` (`models:/credit-risk@staging`) |
| Algorithm | Histogram gradient boosting (`hist_gradient_boosting`), tuned with Optuna (study `hgb-tuning`, best of 30 trials), wrapped in **isotonic calibration** |
| Key settings | learning rate 0.0164, 200 iterations, 4 leaf nodes, min 181 samples per leaf |
| Features | 164 (application fields plus aggregates from bureau, previous applications, POS/cash, installments and credit card tables) |
| Output | Estimated probability that the applicant will have payment difficulties (default) |
| Decision threshold | **0.085**: score ≥ 0.085 → reject, otherwise approve |
| How the threshold was chosen | It minimises expected cost on calibrated **out-of-fold training scores**, with approving a defaulter costing 10 and rejecting a good payer costing 1. The break-even risk for 10:1 costs is 1/11 ≈ 0.091, and the cost search landed at 0.085. The validation split was not used, so its results stay unbiased. |
| Live service | Cloud Run, `https://credit-risk-api-480708713552.us-central1.run.app` (`/predict`); p95 latency about 90 ms over the network |
| Owner | Team 2 (Rithvik, Jayden) |

## Intended use

**For:** loan officers and the lending workflow at a consumer lender. Software calls the
API with an applicant ID (and optionally updated income, credit or annuity amounts) and gets
a default-risk estimate with an approve/reject recommendation. It supports the first
screening of a **new cash or consumer loan application**.

**Decides alone or supports a person?** It **supports a person**. The recommendation is
an input to a loan officer, who makes the final decision. Applications that are borderline
(scores near 0.085) or declined should be reviewable by a person, and declined applicants
should get reasons (see Explanations).

**Not for:**

- Fully automated declines with no human review or appeal.
- Setting interest rates, credit limits or loan amounts. The model was trained only on a
  yes/no outcome.
- Products or populations it never saw: mortgages, business loans, applicants outside the
  Home Credit population, or other countries.
- Collections, marketing, fraud detection, or any decision about existing customers.
- Any use that is unlawful where it is deployed. The model currently uses gender and age
  as inputs (see Fairness).
- Production lending decisions in general: this is a course project trained on a
  5,000-applicant sample.

## Data

- **Source:** the Home Credit Default Risk competition on Kaggle, used under the competition
  rules. The data is not redistributed, and `data/` is not committed.
- **Sample:** 5,000 applicants drawn from the 307,511 in `application_train` (seed 42,
  stratified by target), with all their related records in the six history tables.
- **Split:** a fixed split (`config/split_ids.csv`): **4,000 training** applicants (323
  defaulters) and **1,000 validation** applicants (81 defaulters).
- **One row** is one loan application (`SK_ID_CURR`), with the history tables aggregated to
  one row per applicant.
- **Target:** `TARGET = 1` if the applicant had payment difficulties (8.08% of the sample).
- **Known quirks:**
  - `DAYS_EMPLOYED` holds the impossible sentinel value 365243 (about 1,000 years) for
    unemployed applicants and pensioners. We replace it with missing and add a
    `DAYS_EMPLOYED_ANOM` flag.
  - About a quarter of the cells are missing, and many building columns are more than 70%
    missing.
  - The external scores `EXT_SOURCE_1/2/3`, the strongest features, are often missing
    (`EXT_SOURCE_3` in about 20% of training rows).
  - `DAYS_*` columns count days before the application, so they are negative.

Details are in [data_card.md](data_card.md).

## Performance

All numbers are on the 1,000 validation applicants the model never trained on. They rest on
only **81 defaulters**.

| Metric | Production model | Baseline (logistic regression, application table) |
|---|---|---|
| ROC-AUC [95% CI] | **0.736** [0.682, 0.789] | 0.710 [0.651, 0.767] |
| PR-AUC | 0.213 | 0.169 |
| KS | 0.337 | 0.356 |
| Expected cost per applicant at 0.085 | **0.564** | n/a |

For comparison, the expected cost per applicant is 0.800 when the same model uses a threshold
of 0.5, 0.810 when every applicant is approved, and 0.919 when every applicant is rejected.

- **Approval rate:** 72.9% (it rejects 27.1%).
- **Calibration:** the mean predicted probability is 0.081 against an observed default rate of
  8.1%. Isotonic calibration lowered the Brier score from 0.0695 to 0.0691. The reliability
  curve is in `reports/figures/reliability.png`.
- **Uncertainty:** the AUC interval is about 0.11 wide. The improvement over the baseline
  (+0.026) and over a tuned decision tree (+0.033, paired CI [−0.023, 0.093]) is **not
  statistically conclusive**. With 81 defaulters, a handful of applicants can move every
  metric, and the cost at the threshold could change noticeably on new data.

## Explanations

**Globally** (mean |SHAP|, `reports/explain/shap_global.png`), the model is driven mainly by
the three external credit scores (`EXT_SOURCE_2`, `EXT_SOURCE_3`, `EXT_SOURCE_1`). Next come
time in current employment (`DAYS_EMPLOYED`), the share of earlier applications refused
(`PREV_REFUSED_RATE`), car age, the credit-to-goods ratio, the share of late installments, and
education. Lower external scores, shorter employment and more past refusals or late payments
raise the risk.

**For a declined applicant** (`reports/explain/explanations.md`), SHAP values for that one
applicant are turned into plain-language reasons. Each decline shows its top three
risk-raising features, each with the applicant's value and a typical value, and also what
lowered the risk. Example (borderline decline, score 9.1%): low external credit score 2
(0.271 vs typical 0.564), low external score 3, and a missing external score 1.

Caveats:

- The SHAP values explain the boosting model before calibration. Calibration rescales the
  score but does not reorder applicants.
- Because the external scores dominate, many declines get the same reasons, and those scores
  are opaque to the applicant.
- One example lists "gender is F" as lowering the risk. That is a reason we should not be
  using (see Fairness).

## Fairness

We analysed fairness on the validation set at the 0.085 threshold. Full results are in
[fairness_analysis.md](fairness_analysis.md).

- **Gender:**
  - Men are approved less often than women (65.6% vs 76.5%). This is partly because men
    defaulted more often (13.0% vs 5.7%).
  - But among good payers, men are wrongly declined more often (FPR 31.2% vs 21.2%).
  - Both gaps are clearly real: the 95% intervals do not overlap.
- **Age:**
  - Approval rises from 57.3% (18-29) to 89.5% (60+).
  - Good payers aged 18-29 are declined 41.7% of the time, against 9.3% for those 60+.
  - The model is well calibrated within each age band, so the gap follows the different
    base rates. The approval and FPR gaps between the young and the older bands are clearly
    real.
- **Reliability:** every age band has fewer than 30 defaulters (60+ has 6). All
  "risk caught" (TPR) gaps are within chance, so we cannot yet say whether the model catches
  risk equally well across groups.
- **Proxies:** `CODE_GENDER` and `DAYS_BIRTH` are direct model features. The other 163
  features predict gender with an **AUC of 0.863** (strongest: income, credit-to-income ratio,
  age, `EXT_SOURCE_1`, bureau credit amounts). Removing the gender column would therefore not
  remove gender from the model. Fairness must be measured on outcomes after any change.

## Monitoring

**Logged per decision** (`api/prediction_log.py`, sent to Cloud Logging): request ID, UTC
timestamp, model version, applicant ID, any overrides, all 164 feature values the model
actually saw, the probability, the decision, and the threshold.

**How drift is measured** (`src/monitoring.py`, `python run.py monitor`):

- Each production batch is compared with the 4,000 training rows.
- **PSI** is computed per feature, with training-decile bins plus a bin for missing values.
  PSI ≥ 0.10 is moderate drift and PSI ≥ 0.25 is major.
- The **KS** statistic is computed per numeric feature.
- Missing shares and Evidently reports are checked alongside.
- The score distribution and approval rate are compared with the validation baseline.

**Results so far:**

- **Batch 1** (986 logged requests): no drift (approval 72.0%, score PSI 0.009, no feature
  above 0.10).
- **Batch 2** (1,000 requests) had four features with **major drift**:
  - `AMT_INCOME_TOTAL` (PSI 1.10, mean income 31% lower).
  - The two income ratios that follow from it: `ANNUITY_INCOME_RATIO` (0.47) and
    `CREDIT_INCOME_RATIO` (0.26).
  - `EXT_SOURCE_3` (PSI 0.53), whose missing share rose from 20% to 54%.
  - This pattern suggests an upstream income scaling change and a failing external-score
    feed. Approval fell to 69.1%, but the score PSI stayed small (0.012). That small score
    shift does not show that the model is still accurate.

**Alerts (proposed thresholds):**

- **Major drift:** any feature with PSI ≥ 0.25 → investigate the upstream data before
  trusting the decisions.
- **Moderate drift:** three or more features with PSI ≥ 0.10 → review.
- **Missing values:** a key feature's missing share (`EXT_SOURCE_1/2/3`, income) rises by more
  than 10 points → check the data feed.
- **Approval rate:** moves by more than 5 points from 72.9%, or the score PSI is ≥ 0.10.
- **Fairness:** the lowest/highest approval ratio by gender or age band falls below 0.8.
  Once outcomes arrive, the FPR gap is tracked with Wilson intervals.
- **Logging gaps:** logged predictions fall short of requests served. Batch 1 was missing 14.

Details are in [monitoring_report.md](monitoring_report.md).

## Limitations

- **Small sample:** trained on 4,000 applicants and validated on 81 defaulters. All metrics
  have wide intervals, and small groups (applicants 60+, rare occupations or categories) rest
  on very few people.
- **Data it never saw:** other countries, products or time periods, or applicants whose
  profiles fall outside the training ranges. The 2018 Kaggle data may not reflect today's
  applicants or economy.
- **Changed upstream systems:** the model depends heavily on the external scores and on
  income. Batch 2 shows that a change in income scaling, or a failing `EXT_SOURCE_3` feed,
  changes decisions quietly. The model still returns a confident-looking score. Missing values
  are imputed, not flagged to the user.
- **Unknown live performance:** repayment outcomes take months to arrive, so live AUC, cost
  and calibration are unknown. Monitoring currently only shows that inputs and scores changed,
  not whether decisions got worse.
- **Threshold:** the threshold depends on the assumed 10:1 cost ratio. If the true costs
  differ, the threshold is wrong. There is no "manual review" band yet.
- **Not a real lender's model:** no legal review, no adverse-action process, and not
  validated by a risk team.

## Ethical considerations

**Who is harmed, and how:**

- **Declined good payers (false positives):** applicants who would have repaid are refused
  credit. They lose access to a loan they needed, may turn to more expensive lenders, and
  miss a chance to build a credit history. This harm is not spread evenly: it falls more on
  men and much more on young applicants (42% of young good payers declined).
- **Approved defaulters (false negatives):** the lender loses money, and the borrower takes
  on debt they cannot repay, with collections, fees and damage to their credit record. The
  10:1 cost ratio counts only the lender's loss, not the borrower's.
- **Protected groups:** the model uses gender and age directly. Using sex is prohibited for
  credit decisions in the US (ECOA) and the EU. Using age is restricted. Credit scoring is a
  high-risk system under the EU AI Act.

**What protects them (current and required before any real use):**

- A loan officer makes the final decision; the model only recommends.
- Declined applicants get the top reasons for the decline and a route to **appeal and human
  review**. Borderline scores should go to manual review.
- Remove `CODE_GENDER`, get a legal decision on age, then retrain and re-run the fairness
  analysis.
- Ongoing **monitoring** of drift, approval rates and fairness by group, with alerts.
  Error rates by group are checked once outcomes arrive.
- A named owner and sign-off by the credit-policy, legal and compliance owners before the
  model moves beyond `staging`.
