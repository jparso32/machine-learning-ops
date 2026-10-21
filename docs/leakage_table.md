<!-- PROVIDED template. Copy it to docs/leakage_table.md and fill that copy in:
       cp docs/leakage_table_template.md docs/leakage_table.md      (Windows: copy ...)
     For each feature, answer Yes or No in the third column and give your reason in the fourth.
     Replace every "?" and every "TODO(student)". Keep the table format: python run.py check
     reads it. Add a row for every feature you create, including ones you add yourself. -->

# Leakage table

Team: TODO(student)

**The question for every feature:** at the moment an applicant submits this application,
before we decide, would we already know this value?

If the answer is No, the feature **leaks**: it carries information from the future (often from
the outcome itself). A leaking feature makes validation scores look great and then fails in
real use, because the value does not exist yet when the decision is made.

**How to check, not guess:** the `DAYS_*` and `MONTHS_*` columns count days or months
**relative to this application** (negative = before it). Look at the largest value of each
time column a feature is built from. If it is above 0, part of that feature describes the
future. One look at `df["COL"].max()` is better than an opinion.

## Features you built (and the worked example)

| Feature | Source table | Known at application time? | Why / how you checked |
|---|---|---|---|
| BUREAU_COUNT | bureau | Yes | The bureau report is pulled when the application arrives. Every DAYS_CREDIT in our sample is negative (max -2), so all counted credits were opened before this application. |
| BUREAU_ACTIVE_COUNT | bureau | Yes | Counts existing credits marked active in the available bureau records. |
| BUREAU_CLOSED_COUNT | bureau | Yes | Counts previous credits marked closed in the available bureau records. |
| BUREAU_AMT_CREDIT_SUM_MEAN | bureau | Yes | Averages credit amounts across historical bureau records. |
| BUREAU_AMT_CREDIT_SUM_MAX | bureau | Yes | Finds the maximum credit amount across historical bureau records. |
| BUREAU_AMT_DEBT_MEAN | bureau | Yes | Averages reported debt amounts across historical bureau records. |
| BUREAU_AMT_OVERDUE_SUM | bureau | Yes | Sums overdue amounts reported in the available bureau records. |
| BUREAU_DAYS_OVERDUE_MAX | bureau | Yes | Uses the maximum reported days overdue across historical bureau records. Confirm the source dates do not extend beyond the application date. |
| BUREAU_DAYS_CREDIT_MAX | bureau | Yes | Summarizes the dates of previous credit openings relative to the application. The maximum should be non-positive to support this judgment. |


| Feature | Source table | Available at application? | Reason |
|---|---|---|---|
| PREV_COUNT | previous_application | Yes | Counts the applicant's previous credit applications. |
| PREV_APPROVED_RATE | previous_application | Yes | Calculates the fraction of previous applications recorded as approved. |
| PREV_REFUSED_RATE | previous_application | Yes | Calculates the fraction of previous applications recorded as refused. |
| PREV_AMT_APPLICATION_MEAN | previous_application | Yes | Averages requested amounts from previous applications. |
| PREV_AMT_CREDIT_MEAN | previous_application | Yes | Averages credit amounts associated with previous applications. |
| PREV_DAYS_DECISION_MAX | previous_application | Yes | Summarizes the most recent previous application decision date relative to the current application. Confirm the maximum is non-positive. |
| PREV_DAYS_TERMINATION_MEAN | previous_application | Yes | Averages previous credit termination dates after replacing sentinel values and ensuring the dates do not occur after the current application. |
| PREV_LAST_STATUS` | previous_application | Yes | Uses the status from the most recent previous application. The selected record must be a previous application, not a future event. |


| Feature | Source table | Available at application? | Reason |
|---|---|---|---|
| BB_CREDIT_COUNT | bureau_balance | Yes | Counts historical bureau-balance records associated with the applicant's previous credits. |
| BB_MONTHS_COUNT | bureau_balance | Yes | Counts the available monthly bureau-balance records for previous credits. |
| BB_LATE_MONTHS_COUNT | bureau_balance | Yes | Counts historical months marked late in bureau-balance records. |
| BB_LATE_SHARE | bureau_balance | Yes | Calculates the share of observed historical bureau-balance months marked late. |
| BB_WORST_STATUS | bureau_balance | Yes | Summarizes the worst status reported in the available historical bureau-balance records. |


| Feature | Source table | Available at application? | Reason |
|---|---|---|---|
| POS_LOAN_COUNT | POS_CASH_balance | Yes | Counts the applicant's historical POS cash loans. |
| POS_MONTHS_COUNT | POS_CASH_balance | Yes | Counts monthly records associated with the applicant's POS cash loans. |
| POS_DPD_MAX | POS_CASH_balance | Yes | Uses the maximum days past due recorded in historical POS cash-loan records. |
| POS_DPD_MEAN | POS_CASH_balance | Yes | Averages days past due across historical POS cash-loan records. |
| POS_LATE_SHARE | POS_CASH_balance | Yes | Calculates the share of historical POS cash-loan records indicating late payment. |
| POS_COMPLETED_SHARE | POS_CASH_balance | Yes | Calculates the share of POS cash loans recorded as completed. This is safe only if completion status was known by the application date. |


## Application columns worth a second look

These already sit in `application_train` and went into your Week 1 baseline. Some are less
obvious than they look. Find each one in `HomeCredit_columns_description.csv` (in your
download) before you answer.

| Feature | Source table | Known at application time? | Why / how you checked |
|---|---|---|---|
| TARGET | application_train | No | This is the outcome being predicted. Including it as a model input would directly leak the answer. |
| EXT_SOURCE_2 | application | Yes | This external risk score is available as an applicant feature at application time. |
| DEF_30_CNT_SOCIAL_CIRCLE | application | Yes | Records reported defaults among the applicant's social circle as part of the application data. |
| AMT_REQ_CREDIT_BUREAU_HOUR | application | Yes | Counts credit-bureau requests during the hour preceding the application. |
| DAYS_LAST_PHONE_CHANGE | application | Yes | Records the time since the applicant last changed their phone. Confirm the maximum is non-positive and that the value is measured relative to the application date. |


## Beyond single columns

Leakage can also come from **how** a feature is computed, not only from which column it uses.
In two or three sentences: name one way your feature code could leak even if every column
above is a Yes, and how your code avoids it.

Feature leakage can occur when an aggregation includes records created after the current application, even if each individual column appears reasonable. For example, `POS_COMPLETED_SHARE` could reveal future repayment behavior if it uses a loan's eventual completion status. To avoid leakage, filter historical records to those available at the application date, replace date sentinel values appropriately, exclude `TARGET` from model inputs, and fit preprocessing steps using training data only.
