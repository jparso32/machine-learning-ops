# Fairness tables

Model version 1, threshold 0.085, 1,000 validation applicants. Written by python run.py fairness. Brackets: 95% Wilson interval.

## By gender

| Group | n | Defaulters | Approval rate | Default rate | Mean score | TPR (risk caught) | FPR (good payers declined) | Note |
|---|---|---|---|---|---|---|---|---|
| F | 669 | 38 | 76.5% [73%, 80%] | 5.7% | 0.072 | 60.5% [45%, 74%] | 21.2% [18%, 25%] |  |
| M | 331 | 43 | 65.6% [60%, 70%] | 13.0% | 0.098 | 55.8% [41%, 70%] | 31.2% [26%, 37%] |  |

Largest gaps: approval 0.1097, TPR 0.0471, FPR 0.1001; lowest / highest approval rate: 0.8566.

## By age_band

| Group | n | Defaulters | Approval rate | Default rate | Mean score | TPR (risk caught) | FPR (good payers declined) | Note |
|---|---|---|---|---|---|---|---|---|
| 18-29 | 143 | 16 | 57.3% [49%, 65%] | 11.2% | 0.118 | 50.0% [28%, 72%] | 41.7% [34%, 50%] | fewer than 30 defaulters: TPR unreliable |
| 30-39 | 282 | 28 | 68.4% [63%, 74%] | 9.9% | 0.091 | 67.9% [49%, 82%] | 27.6% [22%, 33%] | fewer than 30 defaulters: TPR unreliable |
| 40-49 | 235 | 18 | 72.8% [67%, 78%] | 7.7% | 0.075 | 61.1% [39%, 80%] | 24.4% [19%, 31%] | fewer than 30 defaulters: TPR unreliable |
| 50-59 | 216 | 13 | 79.6% [74%, 84%] | 6.0% | 0.068 | 53.8% [29%, 77%] | 18.2% [14%, 24%] | fewer than 30 defaulters: TPR unreliable |
| 60+ | 124 | 6 | 89.5% [83%, 94%] | 4.8% | 0.049 | 33.3% [10%, 70%] | 9.3% [5%, 16%] | fewer than 30 defaulters: TPR unreliable |

Largest gaps: approval 0.3217, TPR 0.3452, FPR 0.3241; lowest / highest approval rate: 0.6406.

## Proxy check

Predicting CODE_GENDER (M vs F) from the other 163 features: AUC 0.863 (0.5 = they carry no information about gender). Strongest single features: AMT_INCOME_TOTAL (0.644), CREDIT_INCOME_RATIO (0.599), DAYS_BIRTH (0.593), EXT_SOURCE_1 (0.585), BUREAU_AMT_CREDIT_SUM_MEAN (0.584).
