# API design (Week 5)

Team: 2

## 1. Where the features come from

The model expects 164 columns in a fixed order. Many summarize credit bureau records,
previous applications, monthly balances and payments, so an applicant's form cannot supply
them directly. Asking callers to submit every aggregate would duplicate the training
pipeline in each client and make inconsistent feature definitions likely.

One approach is to query the source tables and calculate all aggregates for every request.
That gives fresher history but increases response time, database load and the complexity of
keeping online calculations identical to training. Another approach is to calculate a
versioned feature store in advance, then retrieve one row by applicant ID. Lookups are fast
and reuse the established pipeline, but the snapshot becomes stale until it is rebuilt.

## 2. The choice for this project

The service uses the precomputed feature store, indexed by `SK_ID_CURR`. Export applies the
same Week 1 cleaning to the Week 2 feature table and retains the registered model's feature
list. A request contains a positive applicant ID and may override `AMT_INCOME_TOTAL`,
`AMT_CREDIT`, or `AMT_ANNUITY` with positive amounts. Omitted or null amounts use the stored
values. The service copies the applicant row before making changes, recomputes the four
dependent ratios when an amount changes, and selects the columns in training order. This
avoids changing the shared store and prevents a new income from being combined with old
income ratios.

## 3. Failure cases

An unknown ID returns HTTP 404 rather than inventing a history. Invalid amounts, missing IDs
and unexpected fields return HTTP 422 before scoring. The model, metadata and feature store
are exported and uploaded together; the metadata records the version, feature list and data
fingerprint. Using a different feature snapshot can silently change predictions, so a
deployment must verify those records rather than replacing individual files independently.

Changes to history after export are not visible to this snapshot. Updating a form amount
does not refresh bureau or payment history. The store and model need a coordinated refresh
when that history changes. A real lending system would also require authentication,
authorization, audit controls and a process for decision review. This project is a course
demonstration on the fixed sample.

## 4. Observed requests

The following responses were captured from the application using the real exported model
on November 13, 2026. Complete response objects are saved in `reports/api_examples.json`.

Valid: `POST /predict` with `{"SK_ID_CURR":100021}` returned HTTP 200:

```json
{"SK_ID_CURR":100021,"probability":0.10431654676258995,"decision":"reject","threshold":0.085,"model_version":"1"}
```

Invalid: `{"SK_ID_CURR":100021,"AMT_INCOME_TOTAL":-1}` returned HTTP 422. The response
named `AMT_INCOME_TOTAL` and said `Input should be greater than 0`.

Unknown: `{"SK_ID_CURR":1}` returned HTTP 404:

```json
{"detail":"Applicant 1 is not in the feature store"}
```
