# HomeShare Opportunity Watcher

Polls https://thehomeshare.ie/opportunities/ roughly every 10-15 minutes via
GitHub Actions and emails a notification whenever a new listing appears.

**This repo is public on purpose:** GitHub Actions minutes are unlimited and
free for public repos, but capped at 2,000 min/month for private ones. At a
10-minute polling interval that cap is exhausted in under two weeks, after
which GitHub blocks further runs until a payment method / spending limit is
added. No secrets live in this repo (they're all GitHub Actions secrets) and
the committed data file only contains public listing slugs, so there's
nothing sensitive exposed by making it public.

**Note on triggering:** GitHub's native `schedule` cron trigger turned out to
be unreliable for this repo in practice — measured averaging ~2 hours between
runs instead of the configured 15 minutes (a known GitHub Actions limitation
for low-activity/private repos, not a bug in this workflow). The primary
trigger is now an external cron service (see step 5 below) that calls the
GitHub API to fire the workflow on a reliable schedule; the `schedule` cron
in the workflow file is kept only as an hourly backup.

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
2. Sign up at https://resend.com and create an API key (free tier covers
   this easily). Note: without verifying a custom sending domain, Resend's
   sandbox sender (`onboarding@resend.dev`) can only deliver to the email
   address you signed up with — that's fine here since notifications go to
   your own inbox anyway.
3. Add these repository secrets (Settings → Secrets and variables → Actions):
   - `RESEND_API_KEY` — the API key from Resend
   - `EMAIL_FROM` — optional, defaults to `HomeShare Watcher <onboarding@resend.dev>`
   - `EMAIL_TO` — `rayraa@outlook.ie` (or wherever notifications should go,
     must match the address you signed up to Resend with unless you've
     verified a custom domain)
4. The workflow at `.github/workflows/check-opportunities.yml` also runs on
   an hourly cron schedule as a backup, automatically once merged to the
   default branch. You can also trigger it manually from the Actions tab
   ("Run workflow").
5. **Set up the reliable external trigger** (recommended — see note above):
   1. Create a fine-grained personal access token at
      https://github.com/settings/personal-access-tokens/new, scoped to
      **only this repository**, with repository permission
      **Contents: Read and write**. Give it an expiration (e.g. 1 year) and
      save the token somewhere safe — GitHub only shows it once.
   2. Sign up for a free account at https://cron-job.org.
   3. Create a new cronjob with:
      - **URL**: `https://api.github.com/repos/raymcdhub/utility/dispatches`
      - **Method**: `POST`
      - **Schedule**: every 10 minutes
      - **Headers**:
        - `Authorization: Bearer <your PAT>`
        - `Accept: application/vnd.github+json`
        - `X-GitHub-Api-Version: 2022-11-28`
        - `Content-Type: application/json`
      - **Body**: `{"event_type": "check-opportunities"}`
   4. Save. A successful trigger returns HTTP 204 with an empty body; check
      the repo's Actions tab to confirm runs are firing every ~10 minutes.

## Local testing

```bash
pip install -r requirements.txt
export RESEND_API_KEY="re_xxxxxxxx"
export EMAIL_FROM="HomeShare Watcher <onboarding@resend.dev>"
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
