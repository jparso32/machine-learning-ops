<!-- PROVIDED: copy this file to docs/runbook.md and fill in every placeholder.
     Written for a teammate who is woken up at 3 am: exact commands, no theory. -->

# Runbook: credit-risk service

Team: TODO · Service: TODO (URL) · Project: TODO · Bucket: TODO

## Who and where

TODO: Who is on call, where the dashboards and logs are (links: Cloud Run service, Logs
Explorer query for drift_alert, Cloud Build history, the bucket's models/ folder).

## 1. A drift alert fires

TODO: How you notice it, the first three things you check (which features, PSI, missing
shares; is it a data bug upstream or a real change in applicants?), when you let the
automated retrain go ahead and when you stop it, and whom you tell.

## 2. The service is slow or failing

TODO: What "slow" means for us (our p95 from Week 5), where to look (Cloud Run metrics and
logs), the usual causes (cold starts, a bad bundle, instance limit), and what to do for each.

## 3. A bad model is serving: roll back

TODO: The exact commands, in order, to put the previous version back (laptop: python run.py
rollback --version N; Cloud Shell: the gcloud run services update command with the folder),
how to check it worked (/model-info), and how long it took when you practised it.

## 4. After an incident

TODO: What you write down, and where.
