# Data card: Home Credit Default Risk (Week 1 sample)

# Data card: Home Credit Default Risk (Week 1 sample)

## 1. Source and license terms

The data comes from Home Credit Group’s Home Credit Default Risk competition on Kaggle and is subject to the competition rules. Each member must accept those rules before downloading. Following the assignment’s restrictions, we do not share or redistribute the data. The repository ignores `data/` and contains code, documentation, and reports instead.

## 2. What each table holds

| Table                 | One row is...                                                | Links by                 |
| --------------------- | ------------------------------------------------------------ | ------------------------ |
| application_train     | One current loan application with its target                 | SK_ID_CURR               |
| bureau                | One previous credit account reported by another institution  | SK_ID_CURR, SK_ID_BUREAU |
| bureau_balance        | One month of history for a bureau credit account             | SK_ID_BUREAU             |
| previous_application  | One previous Home Credit application                         | SK_ID_CURR, SK_ID_PREV   |
| POS_CASH_balance      | One monthly record for a previous point-of-sale or cash loan | SK_ID_CURR, SK_ID_PREV   |
| installments_payments | One payment record for a previous loan installment           | SK_ID_CURR, SK_ID_PREV   |
| credit_card_balance   | One monthly record for a previous credit card account        | SK_ID_CURR, SK_ID_PREV   |

`bureau_balance` does not contain SK_ID_CURR. It links to applicants through SK_ID_BUREAU in `bureau`.

## 3. Full size versus sample size

Sample memory figures are in MB and rounded.

| Table                 |  Full rows | Sample rows | MB before | MB after |
| --------------------- | ---------: | ----------: | --------: | -------: |
| application_train     |    307,511 |       5,000 |       8.2 |      1.6 |
| bureau                |  1,716,428 |      23,680 |       6.5 |      1.2 |
| bureau_balance        | 27,299,925 |     231,091 |      14.5 |      1.3 |
| previous_application  |  1,670,214 |      23,009 |      23.5 |      2.0 |
| POS_CASH_balance      | 10,001,358 |     138,350 |      14.7 |      2.9 |
| installments_payments | 13,605,401 |     186,311 |      11.4 |      5.3 |
| credit_card_balance   |  3,840,312 |      50,668 |      11.2 |      3.8 |

The provided script selects 5,000 applicants using seed 42 and stratifies by TARGET. It keeps all related records for those applicants. Sampling whole applicants preserves their histories and table relationships instead of keeping random, incomplete records.

## 4. Target definition and class balance

TARGET = 1 means the applicant had payment difficulties under the dataset’s definition. It is used as the assignment’s default-risk label.

- Full data: 8.073% positive.
- Sample: 404 of 5,000, or 8.08%.
- Training: 323 of 4,000, or 8.075%.
- Validation: 81 of 1,000, or 8.10%.

The fixed stratified split keeps the class proportions similar so both groups contain examples of payment difficulties.

## 5. Known issues

About 25.1% of the application table’s cells are missing, and 48 columns are more than half empty. COMMONAREA_AVG, COMMONAREA_MODE, and COMMONAREA_MEDI are each 71.42% missing. Many highly missing columns describe buildings or apartments and appear in AVG, MODE, and MEDI groups.

DAYS_EMPLOYED contains the impossible value 365243 for 897 applicants. We replace it with a missing value and add DAYS_EMPLOYED_ANOM to preserve the indicator. Numeric missing values are filled using training medians, and categorical missing values using training modes.

DAYS\_\* values generally count days before the application. A negative DAYS_BIRTH represents age in days; a value closer to zero means a younger applicant. ID columns identify records and are excluded from model inputs.

## 6. Sensitive columns

Gender, age, and family status are sensitive characteristics. Income, occupation, and location may also act as proxies. The baseline includes these available features, so fairness is not established. Before real use, we would compare errors across groups and evaluate whether sensitive features should be removed or restricted. Removing them alone would not eliminate proxy effects.

## 7. Limitations of a small sample

The validation set contains only 81 positive cases, so a few applicants can noticeably change the metrics. We have not calculated confidence intervals, so the exact uncertainty is unknown. Rare categories and smaller demographic groups may be missing or poorly represented. Results from this sample are a baseline and do not establish performance on future applicants.
