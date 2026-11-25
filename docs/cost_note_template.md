<!-- PROVIDED: copy this file to docs/cost_note.md and fill in every placeholder.
     Source: Google Cloud Console -> Billing -> Reports (filter: this project; group by
     service; the last 30 days). Include a screenshot in docs/ if you like. -->

# Cost note

Team: TODO · Project: TODO · Period: TODO (dates)

## What we spent

| Service | Cost so far | What used it |
|---|---|---|
| Cloud Run | TODO | the API, the drift-check function |
| Cloud Build | TODO | CI on every pull request, the retrain builds |
| Artifact Registry | TODO | the API images |
| Cloud Storage | TODO | the bundles, the training data |
| Cloud Logging | TODO | the prediction logs |
| Cloud Scheduler | TODO | the hourly check |
| Total | TODO | (credits used out of $300) |

## What it would cost per month

TODO: Your estimate for running this system for a month as it is (hourly checks, a few
retrains, the traffic of our batches), and for a real lender with, say, 10,000 applications a
day: which costs grow with traffic, which stay fixed, and the largest one. Show the
arithmetic.

## How we kept it cheap

TODO: Min instances 0, max instances 2, the budget alert, what else; and the one change that
would save the most.
