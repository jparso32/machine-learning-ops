# Problem statement

## 1. Who uses the model, and for what decision?

Loan officers use the model to estimate payment difficulty risk before deciding to approve, review, or reject an application. Without it, they would rely on existing lending rules and manual review. We assume this workflow because the current process was not provided.

## 2. The options

Low-risk applications could be approved, uncertain applications sent for manual review, and high-risk applications considered for rejection. A loan officer would handle referrals. Review takes staff time and delays the decision, but its exact cost was not provided. Thresholds still need to be selected and evaluated.

## 3. The cost of approving someone who defaults

Approving someone who does not repay costs the lender 10 cost units per applicant. These are the assignment's units, not a specific dollar amount.

## 4. The cost of rejecting someone who would have repaid

Rejecting someone who would have repaid costs 1 cost unit. Approving a defaulter costs 10 times as much, so the lender should be more cautious about approval. With calibrated probabilities and only approve or reject options, the cost-based rejection threshold would be about 9.1% risk. Manual review and its cost could change this policy.

## 5. Success metrics, and why

ROC-AUC measures how well the model ranks risky applicants. PR-AUC focuses on finding applicants with payment difficulties, and KS measures the largest separation between the two groups' score distributions. Expected cost measures the effect of decisions using the 10:1 costs.

Only 8.08% of the sample had payment difficulties. Predicting no payment difficulties for everyone would give 91.92% accuracy, making accuracy misleading.

Our validation ROC-AUC was 0.710, PR-AUC was 0.169, and KS was 0.356. These are useful

6. Risks and sensitive features

CODE_GENDER and DAYS_BIRTH describe gender and age. Family status is also sensitive. Occupation, income, and location could act as proxies for sensitive characteristics.

A wrong rejection could prevent someone from getting a needed loan. A wrong approval could leave a borrower with debt they cannot repay and cause losses for the lender. We should compare errors across groups before using the model for real decisions.

7. Assumptions

We assume the sample is reasonably representative, TARGET is a useful indicator of repayment risk, and the 10:1 costs fit the assignment. We also assume all model inputs are available when an application is evaluated and that staff review uncertain cases.

The biggest concern is whether future applicants resemble this sample. If they do not, the scores and decision thresholds may not work as expected.
