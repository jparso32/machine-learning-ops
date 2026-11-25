# Demo checklist: 8 minutes

<!-- PROVIDED -->

Rehearse it once, with a timer. One member drives, the others explain. Have every tab open
before you start: the live URL's /docs page, Logs Explorer (query
`jsonPayload.event="drift_alert"`), Cloud Build History, the bucket's `models/` folder, and a
terminal on your laptop.

**The day before:** run the whole loop once (docs/cloud_shell_week7_wednesday.md, step 9),
so a finished retrain build exists to show. Then clear the cooldown:
`gcloud storage rm gs://$BUCKET/monitoring/state.json`.

| Minute | Show | Say |
|---|---|---|
| 0-1 | The live URL: `/health`, `/model-info`, one `/predict` | what the system does, which version serves, and where it runs |
| 1-2 | `python run.py send --batch 3 --drift-income 0.7 --url ...` | "incomes arrive 30% lower, as in batch 2" |
| 2-3 | Cloud Shell: `gcloud scheduler jobs run drift-check --location=us-central1`, then `last_check.json` | which alerts fired, with their PSI, and your thresholds |
| 3-4 | Logs Explorer: the `drift_alert` entry; Cloud Build: the retrain build it started | how the function starts the pipeline, under which identity |
| 4-6 | The finished build from the day before: its steps, `decision.json` in the new `models/vN/` folder | what the pipeline compared, what your gate said, what it decided, and why |
| 6-7 | The promotion (`/model-info` shows the new version) or, if it kept the champion, your rollback drill: point the service at another folder and back | how fast you can undo a bad model |
| 7-8 | Your next steps | what you would change before a real lender used it |

If the cloud misbehaves during the demo: show the finished build from the day before, the
screenshots in docs/automation.md, and say what went wrong. A working fallback is part of
operating a system.
