# Experiment notes (Week 3)

Team: jparso32 and rithvikgottu

## Setup

All runs used the same feature table and fixed split: 4,000 training applicants,
including 323 defaults. We compared models using 5-fold stratified
cross-validation on the training split. The separate validation split was used
for reporting, not for selecting settings.

Data version: f6d247eaeb2f

## Results

Each boosting variation changes one setting from hgb_default.

| Run | What changed from hgb_default | CV AUC +/- std | Train AUC | Valid AUC [95% CI] |
|---|---|---|---|---|
| baseline_lr | Logistic regression baseline | 0.7231 +/- 0.0321 | 0.8455 | 0.7273 [0.6658, 0.7831] |
| tree_unlimited | Decision tree without depth or leaf-size limits | 0.5423 +/- 0.0130 | 1.0000 | 0.5491 [0.5075, 0.5987] |
| tree_tuned | Best decision tree from the CV grid search | 0.6965 +/- 0.0095 | 0.7824 | 0.7026 [0.6450, 0.7558] |
| hgb_default | Nothing | 0.7251 +/- 0.0390 | 1.0000 | 0.6968 [0.6358, 0.7597] |
| hgb_l2 | l2_regularization=1.0 | 0.7321 +/- 0.0328 | 1.0000 | 0.7454 [0.6972, 0.7958] |
| hgb_lr003 | learning_rate=0.03 | 0.7236 +/- 0.0250 | 0.9990 | 0.7419 [0.6899, 0.7928] |
| hgb_leaf15 | max_leaf_nodes=15 | 0.7186 +/- 0.0324 | 0.9996 | 0.7381 [0.6804, 0.7909] |
| hgb_undersample | Keep 3 non-defaulters per defaulter during training | 0.7217 +/- 0.0245 | 0.9987 | 0.7550 [0.6973, 0.8089] |
| hgb_balanced | class_weight=balanced | 0.7125 +/- 0.0446 | 1.0000 | 0.7262 [0.6656, 0.7826] |

## Overfitting

tree_unlimited reached a training AUC of 1.0000 but a CV AUC of only 0.5423,
showing that it memorized the training rows and generalized poorly.
The grid search selected max_depth=5 and min_samples_leaf=50 using CV AUC.
tree_tuned reduced the train-to-CV gap from about 0.458 to 0.086 and improved
CV AUC to 0.6965.

## What helped and what did not

hgb_l2 had the highest CV AUC at 0.7321, beating hgb_default by 0.0070 and
baseline_lr by 0.0090.
hgb_lr003, hgb_leaf15, hgb_undersample, and hgb_balanced all had lower CV AUC
than hgb_default.
These differences are smaller than the fold standard deviations, so the
apparent gains or losses may be noise.
Although hgb_undersample had the highest validation AUC among these runs,
we did not select it using validation performance.
All boosting runs still had training AUC near 1.0, indicating substantial
overfitting.
Next, we would try larger min_samples_leaf values and stronger L2
regularization, comparing settings using training-split CV AUC.
