# HomeShare Opportunity Watcher

Polls https://thehomeshare.ie/opportunities/ every 15 minutes via GitHub Actions
and emails a notification whenever a new listing appears.

## How it works

- `check_opportunities.py` scrapes the opportunities page, extracts each
  listing's title and URL (keyed by its URL slug), and diffs against
  `data/seen_opportunities.json`.
- Any slugs not already in that file are "new" — an email is sent listing
  their title + URL, and the file is updated and committed back to the repo
  by the workflow so state persists between runs.
- **First run is a bootstrap**: it saves whatever is currently live without
  sending an email (otherwise every existing listing would look "new").
  After that, only genuinely new listings trigger a notification.

## Setup

1. Push this repo to GitHub (already done if you're reading this there).
2. Add these repository secrets (Settings → Secrets and variables → Actions):
   - `SMTP_USERNAME` — your Outlook.com email address (e.g. `rayraa@outlook.ie`)
   - `SMTP_PASSWORD` — an **app password** for that account, not your normal
     login password. Generate one at
     https://account.live.com/proofs/AppPassword (requires two-step
     verification to be turned on for the Microsoft account first).
   - `EMAIL_FROM` — usually the same as `SMTP_USERNAME`
   - `EMAIL_TO` — `rayraa@outlook.ie` (or wherever notifications should go)
3. The workflow at `.github/workflows/check-opportunities.yml` runs on a
   `*/15 * * * *` cron schedule automatically once merged to the default
   branch. You can also trigger it manually from the Actions tab
   ("Run workflow").

## Local testing

```bash
pip install -r requirements.txt
export SMTP_USERNAME="rayraa@outlook.ie"
export SMTP_PASSWORD="xxxx-xxxx-xxxx-xxxx"   # app password
export EMAIL_FROM="rayraa@outlook.ie"
export EMAIL_TO="rayraa@outlook.ie"
python check_opportunities.py
```

Delete `data/seen_opportunities.json` to force a re-bootstrap, or remove a
slug from it to simulate a "new" listing and test the email path.

## Notes

- GitHub Actions' `schedule` cron is best-effort — during high load it can
  fire a few minutes late, but it will not run more often than every 15
  minutes.
- The workflow needs `contents: write` permission (already set) to commit
  the updated state file back to the repo after each run.
