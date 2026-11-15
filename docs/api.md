# Credit-risk scoring API

Team: 2

Live base URL: https://credit-risk-api-480708713552.us-central1.run.app .
Interactive documentation: https://credit-risk-api-480708713552.us-central1.run.app/docs .
Local development uses `http://127.0.0.1:8000` after `python run.py serve`.

The live service is revision `credit-risk-api-00001-dbs`, model version `1`. Health and
model metadata are verified. Applicant `100021` returned HTTP 200, probability
`0.10431654676258995`, and `reject` at threshold `0.085`; negative income returned 422,
and unknown applicant `1` returned 404. The Wednesday checkpoint passed.

## Endpoints

Set `BASE_URL` to the live service for these requests. The responses show the key model
fields and error formats; the corresponding live success and error statuses are verified.

```bash
BASE_URL=https://credit-risk-api-480708713552.us-central1.run.app
```

### GET /health

Reports whether startup completed and a model is loaded. It does not score an applicant.

```bash
curl "$BASE_URL/health"
```

```json
{"status":"ok","model_loaded":true,"model_version":"1"}
```

### GET /model-info

Identifies the serving model and its decision threshold so a response can be traced to a
specific model and feature snapshot.

```bash
curl "$BASE_URL/model-info"
```

```json
{"name":"credit-risk","version":"1","threshold":0.085,"n_features":164,"valid_auc":0.735588871424925,"data_version":"c393a114d6e3","exported":"2026-11-13T19:03:41+00:00"}
```

### POST /predict

Scores one applicant in the 5,000-row feature store. Supply the positive integer
`SK_ID_CURR`. Optional `AMT_INCOME_TOTAL`, `AMT_CREDIT`, and `AMT_ANNUITY` must be positive
numbers when supplied; omitted or null amounts retain their stored values. Amount changes
are applied to a copy of the row and the dependent ratios are recomputed. No history is
created for an ID outside the snapshot.

```bash
curl -X POST "$BASE_URL/predict" -H 'Content-Type: application/json' \
  -d '{"SK_ID_CURR":100021}'
```

```json
{"SK_ID_CURR":100021,"probability":0.10431654676258995,"decision":"reject","threshold":0.085,"model_version":"1"}
```

The probability estimates default risk. A probability greater than or equal to 0.085
returns `reject`; a lower probability returns `approve`. These are course demonstration
outputs from a fixed dataset.

## Errors

HTTP 422 means the request does not satisfy the schema. A missing or invalid ID, an amount
of zero or less, text instead of a numeric amount, or an unexpected field is rejected before
scoring. For example:

```bash
curl -X POST "$BASE_URL/predict" -H 'Content-Type: application/json' \
  -d '{"SK_ID_CURR":100021,"AMT_INCOME_TOTAL":-1}'
```

```json
{"detail":[{"type":"greater_than","loc":["body","AMT_INCOME_TOTAL"],"msg":"Input should be greater than 0","input":-1,"ctx":{"gt":0.0}}]}
```

HTTP 404 means the request is valid but the applicant is absent from the store:

```bash
curl -X POST "$BASE_URL/predict" -H 'Content-Type: application/json' \
  -d '{"SK_ID_CURR":1}'
```

```json
{"detail":"Applicant 1 is not in the feature store"}
```

## Response times

Measured from the client Mac on November 15, 2026 with
`python run.py latency --url https://credit-risk-api-480708713552.us-central1.run.app --n 100`.
The service received no test requests for 20 minutes, from 16:47:11 to 17:07:11 UTC,
before the first measured request. The first request was timed separately; the next
100 requests were used for the warm response-time summary.

| Measurement | Result |
|---|---:|
| First request after idle | 172.3 ms |
| Warm requests | 100 |
| Warm p50 | 73.79 ms |
| Warm p95 | 89.72 ms |
| Warm maximum | 100.11 ms |
| Warm mean | 75.74 ms |
| HTTP errors | 0 |

`reports/latency.json` contains the actual measurements. These are client-to-service
times, including network travel to Google Cloud. p50 is the median wait; p95 shows the
slower end of the response times that an applicant could experience.

## Online or batch scoring?

Online scoring answers one applicant when a form is submitted. It suits an interactive
credit application because the applicant can receive a response while still on the screen.
It needs a continuously reachable service, predictable latency, and clear failure handling.
Scaling to zero reduces idle resource use but introduces startup delay after quiet periods.
Batch scoring processes many applicants on a schedule and can share startup and processing
costs across the whole group. It is useful for periodic portfolio monitoring or refreshing
stored scores when an immediate answer is unnecessary. Its tradeoff is that a score can be
out of date between runs. For this course's single-application decision, online scoring
fits the interaction, while a scheduled batch pipeline can refresh the feature snapshot.
