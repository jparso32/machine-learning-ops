# Champion or challenger

Champion version 1 (threshold 0.085), challenger version 2 (threshold 0.075). Each model at its own threshold. Intervals: 95% paired bootstrap of challenger minus champion. Written by python run.py champion.

## The validation slice (1000 applicants, 81 defaults)

| | AUC | Cost per applicant | Approval rate | Bad rate among approved |
|---|---|---|---|---|
| champion | 0.736 | 0.564 | 72.9% | 4.7% |
| challenger | 0.743 | 0.531 | 55.3% | 2.7% |
| difference [95% interval] | +0.008 [-0.021, +0.038] | -0.033 [-0.124, +0.062] | | |

## The recent slice (564 applicants, 72 defaults)

| | AUC | Cost per applicant | Approval rate | Bad rate among approved |
|---|---|---|---|---|
| champion | 0.744 | 0.668 | 69.1% | 6.4% |
| challenger | 0.729 | 0.704 | 48.0% | 5.9% |
| difference [95% interval] | -0.014 [-0.041, +0.016] | +0.035 [-0.089, +0.133] | | |

## Quality gate on the challenger

FAILED: 1 model tests failed, limit 0.
(model tests: {'passed': 2, 'failed': 1, 'xfail': 1, 'skipped': 0})

## Decision: KEEP

- gate: 1 model tests failed, limit 0.
