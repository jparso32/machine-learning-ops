# Week 7 in Cloud Shell: wire the automated loop

<!-- PROVIDED -->

```
Cloud Scheduler (every hour)
   │  calls, with its own identity
   ▼
drift-check (Cloud Run function) ── reads the last hour of prediction logs (Cloud Logging)
   │                                 and drift_reference.json from your bucket
   │  if YOUR alerts fire: logs a drift_alert, starts ...
   ▼
retrain trigger (Cloud Build, cloudbuild_retrain.yaml)
   data ─▶ retrain + compare + YOUR gate + YOUR decide ─▶ registers models/vN/
   │
   └─ only if "promote": the service now loads models/vN/
```

**One member** runs this, in order, in **Cloud Shell**. Allow about 45 minutes the first
time (most of it waiting for deploys and the first build). Before you start: Monday's
`docs/cloud_shell_week7.md` steps 1-2 are done (the service loads `models/v1/` or `v2/`), and
your Wednesday pull request (with `functions/`, `cloudbuild_retrain.yaml`, and your filled-in
`config/alerts.yaml` and `reports/monitoring/drift_reference.json`) is **merged into main**.

## 0. Settings (every time Cloud Shell opens or reconnects)

```bash
gcloud config set project <your-project-id>
PROJECT=$(gcloud config get-value project)
REGION=us-central1
BUCKET=<your bucket's name>
URL=$(gcloud run services describe credit-risk-api --region=$REGION --format='value(status.url)')
BUILD_SA=$(gcloud builds triggers describe pr-checks --format='value(serviceAccount)' | sed 's|.*/||')
FN_SA=drift-check@$PROJECT.iam.gserviceaccount.com
API_SA=credit-risk-api@$PROJECT.iam.gserviceaccount.com
echo "$BUCKET | $URL | $BUILD_SA"
```

**Check:** three values. `BUILD_SA` is the service account your Week 4 `pr-checks` trigger
uses (an email). If it is empty, open **Cloud Build → Triggers → pr-checks**, copy the
service account email shown there, and set `BUILD_SA=<that email>` by hand.

## 1. Turn on the services (once, 1-2 minutes)

```bash
gcloud services enable cloudfunctions.googleapis.com cloudscheduler.googleapis.com \
    cloudbuild.googleapis.com run.googleapis.com logging.googleapis.com
```

## 2. Put the training data and the reference in the bucket (Console, 5 minutes)

Cloud Build has no data of its own: the retrain step reads it from your **private** bucket.
In **Cloud Storage → Buckets →** your bucket:

1. **Create folder** `training` → open it → **Upload files**: from your repository,
   `data/features/features.parquet`, `data/production/store_extension.parquet`,
   `data/production/labels.parquet`.
2. Back at the top: **Create folder** `monitoring` → open it → **Upload files**:
   `reports/monitoring/drift_reference.json`.

```bash
gcloud storage ls gs://$BUCKET/training/ gs://$BUCKET/monitoring/
```

**Check:** three files under `training/`, one under `monitoring/`. The bucket stays private:
these files hold data derived from the Kaggle data.

## 3. Let the build do its job (once)

The retrain build must read and write your bucket, and update the service (acting as the
service's own account):

```bash
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
    --member=serviceAccount:$BUILD_SA --role=roles/storage.objectAdmin
gcloud projects add-iam-policy-binding $PROJECT \
    --member=serviceAccount:$BUILD_SA --role=roles/run.developer --condition=None
gcloud iam service-accounts add-iam-policy-binding $API_SA \
    --member=serviceAccount:$BUILD_SA --role=roles/iam.serviceAccountUser
```

**Check:** each prints a policy that contains `$BUILD_SA` with that role.

## 4. Create the retrain trigger (Console, 3 minutes)

**Cloud Build → Triggers → Create trigger** (region **global**, as in Week 4):

1. **Name:** `retrain`. **Event:** **Manual invocation**.
2. **Source:** your repository (the one connected in Week 4), **Branch:** `main`.
3. **Configuration:** Cloud Build configuration file, location **Repository**, file
   `cloudbuild_retrain.yaml`.
4. **Advanced → Substitution variables → Add variable:** `_BUCKET` = your bucket's name
   (no `gs://`).
5. **Service account:** the same one as `pr-checks` (`$BUILD_SA`). **Create**.

```bash
TRIGGER_ID=$(gcloud builds triggers describe retrain --format='value(id)')
echo $TRIGGER_ID
```

## 5. Run the pipeline once by hand (8-12 minutes)

```bash
gcloud builds triggers run retrain --branch=main
```

Watch it in **Cloud Build → History** (click the running build). Step `data` copies the data,
`retrain` installs the packages (the slowest part) and runs your code, `deploy` either
promotes or prints `KEPT`. When it is green:

```bash
gcloud storage ls gs://$BUCKET/models/
gcloud storage cat "$(gcloud storage ls gs://$BUCKET/models/ | tail -1)decision.json" | head -20
```

**Check:** a new folder `models/vN/` with four files, and its `decision.json`. Copy the
build's URL (the browser's address bar) into `docs/automation.md`.

## 6. The function's own account (once)

The function needs to read the logs, read and write the `monitoring/` files, and start the
trigger (which runs as `$BUILD_SA`), and nothing else:

```bash
gcloud iam service-accounts create drift-check --display-name="Drift check"
sleep 45   # a new account takes up to a minute to be visible everywhere
gcloud projects add-iam-policy-binding $PROJECT \
    --member=serviceAccount:$FN_SA --role=roles/logging.viewer --condition=None
gcloud projects add-iam-policy-binding $PROJECT \
    --member=serviceAccount:$FN_SA --role=roles/cloudbuild.builds.editor --condition=None
gcloud storage buckets add-iam-policy-binding gs://$BUCKET \
    --member=serviceAccount:$FN_SA --role=roles/storage.objectAdmin
gcloud iam service-accounts add-iam-policy-binding $BUILD_SA \
    --member=serviceAccount:$FN_SA --role=roles/iam.serviceAccountUser
```

## 7. Deploy the function (3-5 minutes)

```bash
cd ~ && rm -rf <repo> && git clone https://github.com/<your-account>/<repo>.git && cd <repo>
gcloud functions deploy drift-check --gen2 --region=$REGION --runtime=python311 \
    --source=functions/drift_check --entry-point=check --trigger-http \
    --no-allow-unauthenticated --service-account=$FN_SA \
    --set-env-vars=BUCKET=$BUCKET,TRIGGER_ID=$TRIGGER_ID,SERVICE=credit-risk-api \
    --memory=512Mi --timeout=300s
FN_URL=$(gcloud functions describe drift-check --gen2 --region=$REGION --format='value(serviceConfig.uri)')
curl -s -H "Authorization: bearer $(gcloud auth print-identity-token)" $FN_URL
```

**Check:** the `curl` answers JSON with `"requests"` (probably 0: no traffic in the last hour)
and `"retrain": "not needed"`. `--no-allow-unauthenticated`: nobody on the internet can call
it; you can, as the project owner, and the scheduler can, with the right below.

## 8. The schedule (2 minutes)

```bash
gcloud functions add-invoker-policy-binding drift-check --region=$REGION \
    --member=serviceAccount:$FN_SA
gcloud scheduler jobs create http drift-check --location=$REGION \
    --schedule="0 * * * *" --uri=$FN_URL --http-method=POST \
    --oidc-service-account-email=$FN_SA --oidc-token-audience=$FN_URL
gcloud scheduler jobs run drift-check --location=$REGION
```

`0 * * * *` = at minute 0 of every hour. `jobs run` runs it now instead of waiting.

**Check:** a few seconds later,
`gcloud storage cat gs://$BUCKET/monitoring/last_check.json` shows the new `checked_at`.

## 9. Rehearse the whole loop (the demo, 15 minutes)

1. Laptop: drifted traffic (batch 3, incomes 30% lower, as in batch 2):

   ```
   python run.py send --batch 3 --drift-income 0.7 --url <your service URL>
   ```

2. Cloud Shell, a minute later (log entries take a few seconds to arrive):

   ```bash
   gcloud scheduler jobs run drift-check --location=$REGION
   sleep 30
   gcloud storage cat gs://$BUCKET/monitoring/last_check.json
   ```

   **Check:** `"alerts"` lists your alerts (income, the ratios) and `"retrain"` says
   `started build ...`.

3. **Logging → Logs Explorer**, query `jsonPayload.event="drift_alert"`: the alert, with
   severity WARNING.
4. **Cloud Build → History:** the retrain build started by the function. When it finishes:
   `curl -s $URL/model-info` shows the version that serves now (the new one if promoted).

Before the demo itself, clear the cooldown, or the function will not start a second build
within 6 hours:

```bash
gcloud storage rm gs://$BUCKET/monitoring/state.json
```

## When something goes wrong

| What you see | Why, and what to do |
|---|---|
| `BUILD_SA` empty | Set it by hand from Cloud Build → Triggers → pr-checks (step 0) |
| `Service account ... does not exist` right after creating it | Wait a minute and run the command again |
| Function deploy: "missing permission ... build service account" | Grant the build account it names: `gcloud projects add-iam-policy-binding $PROJECT --member=serviceAccount:<that account> --role=roles/cloudbuild.builds.builder`, then deploy again |
| `curl` to the function: 403 | Use `Authorization: bearer $(gcloud auth print-identity-token)`; the function is private on purpose |
| Function answers 500, "alert thresholds not set" | `config/alerts.yaml` still has nulls: fill it, `python run.py reference`, upload the new `drift_reference.json` (step 2) |
| Function answers 500, "drift_reference.json not found" | Step 2: it must be at `monitoring/drift_reference.json` in the bucket |
| `last_check.json` says `"requests": 0` after sending | The function looks at the last 60 minutes: send, wait a minute, run the job again |
| `"retrain": "skipped: ... cooldown"` | A build was started less than `cooldown_hours` ago: `gcloud storage rm gs://$BUCKET/monitoring/state.json` |
| Function error `403 ... cloudbuild` | Step 6: `cloudbuild.builds.editor` for `$FN_SA`, and `serviceAccountUser` on `$BUILD_SA` |
| Build step `data`: `403 ... storage` | Step 3, first command |
| Build step `deploy`: `PERMISSION_DENIED ... iam.serviceaccounts.actAs` | Step 3, third command |
| Build step `retrain` fails in `pip install` | Rerun it (a download hiccup); if it repeats, send the instructor the red lines |
| Build step `retrain`: `FileNotFoundError ... reports/...json` | Commit and merge `reports/` (final_model.json, champion.json, optuna_best.json): the build reads them from GitHub |
| Scheduler: "App Engine application ... required" | Older projects only: `gcloud app create --region=us-central` once, then create the job again |
