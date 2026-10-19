<!-- PROVIDED template. Copy it to docs/data_card.md and fill that copy in:
       cp docs/data_card_template.md docs/data_card.md
     Replace every line with your answer. `python run.py check` fails while any remain.
     Aim for about one page. Use numbers from your own reports/ files. -->

# Data card: Home Credit Default Risk (Week 1 sample)

## 1. Source and license terms

*Where does the data come from, and who published it? What do the Kaggle competition
rules allow and forbid (for example sharing or redistributing the data)? How does this
repository respect those rules?*

The data comes from the Home Credit Default Risk Kaggle competition, published by Home Credit and hosted by Kaggle. The competition rules govern how the data can be used and shared, so this repository should avoid redistributing the original dataset and should document the source and any processing performed.

## 2. What each table holds

*One line per table: what one row represents and the key column(s) that link it to the
others. Note which table does not carry the applicant id, and how it links instead.*

| Table | One row is... | Links by |
|---|---|---|
| application_train | One applicant and their repayment outcome | SK_ID_CURR |
| bureau | One credit record from another financial institution | SK_ID_CURR, SK_ID_BUREAU |
| bureau_balance | One month's status for a bureau credit record | SK_ID_BUREAU |
| previous_application | One previous loan application | SK_ID_CURR, SK_ID_PREV |
| POS_CASH_balance | One monthly point-of-sale or cash-loan record | SK_ID_CURR, SK_ID_PREV |
| installments_payments | One installment payment record | SK_ID_CURR, SK_ID_PREV |
| credit_card_balance | One monthly credit-card record | SK_ID_CURR, SK_ID_PREV |

## 3. Full size versus sample size

*How many rows does each table have in the full download and in your sample? How much
memory does the sample use before and after shrinking the dtypes
(reports/table_summary.json)? How was the sample chosen, and why sample whole applicants
instead of random rows?*

| Table | Sample Rows | Full Dataset Rows |
|---|---:|---:|
| `application_train` | 5,000 | 307,511 |
| `bureau` | 23,680 | 1,716,428 |
| `bureau_balance` | 231,091 | 27,299,925 |
| `previous_application` | 23,009 | 1,670,214 |
| `POS_CASH_balance` | 138,350 | 10,001,358 |
| `installments_payments` | 186,311 | 13,605,401 |
| `credit_card_balance` | 50,668 | 3,840,312 |

Memory usage was also reduced through data type optimization. For example, application_train decreased from 8.20 MB to 1.56 MB, while bureau_balance decreased from 14.55 MB to 1.32 MB. These reductions make the sample easier to process with limited computing resources.

## 4. Target definition and class balance

*What does TARGET = 1 mean? What is the default rate in the full data, in your sample,
and in each split? Why does the split keep the rates similar?*

TARGET = 1 means the applicant had payment difficulties, while TARGET = 0 means they did not. About 8% of applicants default, making the target imbalanced; report the exact default rates for the full data, sample, training split, and validation split from your results. Keeping the rates similar makes the training and validation comparison more meaningful.

## 5. Known issues

*Missing values (which columns, how much), odd or placeholder values (look closely at
DAYS_EMPLOYED), units and sign conventions (what does a negative DAYS_BIRTH mean?), and
anything else that surprised you in the EDA.*

Several columns have missing values, especially building and housing features such as COMMONAREA_AVG, NONLIVINGAPARTMENTS_AVG, and LIVINGAPARTMENTS_AVG. DAYS_EMPLOYED contains the impossible placeholder value 365243, which should be treated as missing or flagged separately. Negative DAYS_BIRTH and other DAYS_* values represent days before the application, not negative ages or durations. Missing values and unusual values must be handled before model training.

## 6. Sensitive columns

*Which columns describe sensitive characteristics, or could act as a proxy for them?
How do you plan to handle them?*

CODE_GENDER and DAYS_BIRTH describe sensitive characteristics, while income, occupation, and housing features could act as proxies for demographic or socioeconomic differences. We should check model performance and error rates across groups and consider fairness risks before using these features to support lending decisions.

## 7. Limitations of a small sample

*The validation set has about 80 defaults. How much could your metrics move by chance?
What could the sample miss that the full data would show (for example rare categories)?*

The validation set contains about 80 defaults, so a few predictions can noticeably change the evaluation metrics. A 5,000-applicant sample may also miss rare categories and unusual applicant types found in the full dataset. Results from this sample may not generalize to all applicants, so the model should be tested on more data before real-world use.
