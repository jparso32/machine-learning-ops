<!-- PROVIDED: copy this file to docs/modeling_report.md and fill in every placeholder
     (the check fails while the word in capitals below is still anywhere in the file).
     1 to 2 pages. Every number comes from reports/final_model.json, reports/threshold.json,
     or the MLflow UI. Quote every AUC with its 95% interval. -->

# Modeling report (Week 3)

Team: Rithvik, Jayden

## 1. The production model

Which model, which settings (from which Optuna trial), how many features, which
calibration, which threshold, and its registered name and version
(for example `models:/credit-risk@staging`, version 3).
## Final Model

- **Model:** Histogram-based Gradient Boosting (`hist_gradient_boosting`)
- **Optuna study:** `hgb-tuning`
- **Best Optuna trial:** 27 out of 30 trials
- **Hyperparameters:**
  - `learning_rate`: 0.01638
  - `max_iter`: 200
  - `max_leaf_nodes`: 4
  - `min_samples_leaf`: 181
  - `l2_regularization`: 0.03534
  - `max_features`: 0.90531
- **Number of features:** 164
- **Calibration method:** Isotonic
- **Decision threshold:** 0.085
- **Misclassification costs:** 10 for approving a defaulter and 1 for rejecting a good applicant
- **Cross-validation AUC:** 0.7481 ± 0.0193
- **Validation AUC:** 0.7356 (95% CI: 0.6817–0.7890)
- **Validation cost per applicant:** 0.564 at the selected threshold, compared with 0.800 at a threshold of 0.5
- **Registered model name:** `credit-risk`
- **Registered version:** 1
- **MLflow alias:** `staging`
- **Model URI:** `models:/credit-risk@staging`

## 2. Production model against the decision tree

| Metric | Production model | `tree_tuned` |
|---|---:|---:|
| Validation ROC-AUC [95% CI] | 0.736 [0.682, 0.789] | 0.703 [0.645, 0.756] |
| CV ROC-AUC (train split) | 0.748 ± 0.019 | 0.697 ± 0.010 |
| Latency p95, one applicant (ms) | 23.38 | 22.32 |
| Model size (KB) | 245.54 | 17.66 |
| Features | 164 | 164 |
| Explainability | Lower: boosting model with 164 features | Higher: decision tree with `max_depth=5` and `min_samples_leaf=50` |

The AUC difference and its paired 95% interval (from `python run.py final`). Is the
production model better by more than chance? Then justify the choice on all four
dimensions: AUC, speed, size, and explainability. What do you give up compared with the
tree, and why is it worth it (or not)?

The production model's AUC is 0.0330 higher than `tree_tuned`, with a paired 95% confidence interval of [-0.0230, 0.0934], so we cannot conclude that it is better than chance at the 5% significance level.

The production model has better AUC (0.7356 vs. 0.7026) but slightly slower p95 latency (23.38 vs. 22.32 ms), a much larger model size (245.54 vs. 17.66 KB), and lower explainability; I accept these trade-offs for improved predictive performance, although the AUC improvement is not statistically conclusive.

## 3. The decision threshold

The threshold, the costs it comes from, and why it is so far from 0.5. Which scores
was it chosen on, and why not the validation split? Expected cost per applicant on the
validation split at your threshold, at 0.5, and when approving everyone. What share of
applicants does it reject?

The selected threshold is **0.085**, chosen using misclassification costs of 10 for approving a defaulter and 1 for rejecting a good applicant, making it lower than 0.5 because approving a defaulter is much more costly.

The threshold was selected using calibrated out-of-fold predictions on the training split to avoid tuning it on the validation data and producing an overly optimistic evaluation.

On the validation split, the expected cost per applicant was **0.564** at the selected threshold, **0.800** at 0.5, and **0.810** when approving everyone, while the model rejected **27.1%** of applicants at the selected threshold.

## 4. Calibration

Method, Brier score before and after, and what the reliability plot
(`reports/figures/reliability.png`) shows. Did calibration help this model? Why does the
threshold depend on it?

The model used **isotonic calibration**, which improved the Brier score from **0.06946 to 0.06913**, indicating a small improvement in probability accuracy; the reliability plot compares predicted probabilities with observed default rates before and after calibration.

Calibration matters because the decision threshold of **0.085** assumes predicted scores represent actual default probabilities, which are needed to apply the misclassification costs of 10 for approving a defaulter and 1 for rejecting a good applicant.

## 5. Limitations and risks

At least three, for example: the size of the validation set (81 defaults), choices
made on the same train split, what the costs leave out, and sensitive features (Week 1).

- **Limited validation data:** The validation split contains only 81 defaults, so AUC estimates and confidence intervals may be uncertain and may not generalize to future applicants.
- **Potential overfitting during model selection:** Hyperparameter tuning, calibration, and threshold selection use the same training split, so the final model may perform differently on unseen data.
- **Simplified misclassification costs:** The cost function assigns a cost of 10 to approving a defaulter and 1 to rejecting a good applicant but does not capture all real-world financial, operational, or customer impacts.
- **Sensitive features and fairness:** The model may use sensitive or proxy features that contribute to demographic disparities, so fairness should be evaluated across relevant groups before deployment.