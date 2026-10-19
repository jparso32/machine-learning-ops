<!-- PROVIDED template. Copy it to docs/problem.md and fill that copy in:
       cp docs/problem_template.md docs/problem.md
     Replace every line with your answer. `python run.py check` fails while any remain.
     Keep the headings. Delete the italic questions once you have answered them if you like. -->

# Problem statement

Team: Rithvik Gottumukkala, Jayden Parsons, Govardhan Vyloppully

## 1. Who uses the model, and for what decision?

*Who looks at the model's output? What decision do they make with it, and when in the
application process? What happens today without a model?*

Loan officers use the model to estimate whether an applicant will default and help decide whether to approve, reject, or review a loan application. Without the model, they rely on existing rules and applicant information.

## 2. The options

*The decision has three outcomes: approve, refer for manual review, or reject. When should
each one happen? Who handles a referral, and what does a referral cost in time or money?*

Low-risk applicants can be approved, high-risk applicants can be rejected, and uncertain cases can be referred to a loan officer for manual review. Manual reviews take extra time and delay the decision.

## 3. The cost of approving someone who defaults

*Use the cost numbers on the instructor's task card. What does the lender lose when a
borrower who was approved does not repay? State the number and its unit.*

Approving someone who defaults costs the lender 10 units because the borrower does not repay the loan as expected.

## 4. The cost of rejecting someone who would have repaid

*Use the cost numbers on the task card. What does the lender lose by turning away a good
customer? How does this compare with the cost in section 3, and what does that ratio
mean for where you put the decision threshold?*

Rejecting someone who would have repaid costs the lender 1 unit in lost business. Since approving a defaulter costs ten times more, the lender should be cautious when approving loans but avoid rejecting too many reliable borrowers.

## 5. Success metrics, and why

*Which metrics will you report (ROC-AUC, PR-AUC, KS, expected cost)? What does each one
tell you that the others do not? Why is accuracy a poor choice when about 8 percent of
applicants default? What result would count as good enough to be useful?*

We will use ROC-AUC, PR-AUC, KS, and expected cost to measure how well the model ranks risk and how costly its decisions are. Accuracy is misleading because predicting that nobody defaults would still achieve about 92% accuracy when only 8% default, so a useful model must identify risky applicants and reduce expected costs.

## 6. Risks and sensitive features

*Which columns describe protected or sensitive characteristics (for example gender or
age)? Which other columns could stand in for them? Who could be harmed by a wrong
decision, and how?*

CODE_GENDER and DAYS_BIRTH describe sensitive characteristics, while income, occupation, and housing information could indirectly reflect them. Incorrect predictions could unfairly deny loans to reliable applicants, so we should check whether the model treats demographic groups unfairly.

## 7. Assumptions

*What are you assuming about the data, the costs, and how the model will be used? Which
assumption, if it were wrong, would change your approach the most?*

We assume the historical data represents future applicants and that the 10:1 cost ratio reflects the lender's priorities. If the data is biased or the costs are inaccurate, the model's decisions may need to change.
