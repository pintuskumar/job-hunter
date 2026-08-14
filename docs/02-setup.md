# Setup Guide

Complete setup from scratch to a running daily email system.

---

## Prerequisites

- **Python 3.11+** installed
- A **Gmail account** for sending emails (prefer a secondary one, not your main)
- 10 minutes to get API keys

---

## Step 1: Install Python Dependencies

```bash
cd "D:/VSCode/job scraper"
pip install -r requirements.txt
```

Or with explicit Python path (Windows):
```bash
"C:/Users/you/AppData/Local/Programs/Python/Python313/python.exe" -m pip install -r requirements.txt
```

---

## Step 2: Get API Keys

### 2a. RapidAPI Key (for JSearch)

JSearch aggregates LinkedIn + Indeed + Glassdoor. **Free tier: 200 requests/month.**

1. Sign up at **https://rapidapi.com**
2. Subscribe to **JSearch**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
3. Pick the **Free (Basic)** plan
4. Copy your `X-RapidAPI-Key` from the dashboard

### 2b. Hunter.io (optional — currently not used)

Was used for finding contact emails. Replaced with LinkedIn search URLs.
Key stays in `.env` for future use but can be empty.

### 2c. SMTP credentials

Required for sending the daily digest email.

Use an SMTP provider that supports implicit TLS or STARTTLS. If using Gmail,
create an App Password; never use your normal account password.

---

## Step 3: Create `.env` File

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# JSearch (RapidAPI) — required
RAPIDAPI_KEY=your_rapidapi_key_here
JSEARCH_MONTHLY_LIMIT=200
JSEARCH_MONTHLY_RESERVE=20

# Hunter.io — optional, not currently used
HUNTER_API_KEY=

# Generic SMTP — required for daily email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_STARTTLS=true
SMTP_USER=your_smtp_username
SMTP_PASS=your_smtp_password
SMTP_FROM_EMAIL=sender@example.com
RECIPIENT_EMAIL=candidate@example.com

# Daily digest timing (IST timezone)
ENABLE_SCHEDULER=false
DAILY_EMAIL_HOUR=9
DAILY_EMAIL_TIMEZONE=Asia/Kolkata
DAILY_JOBS_COUNT=15

# Required for a public deployment
APP_USERNAME=jobhunter
APP_PASSWORD=replace_with_a_long_random_password
REQUIRE_AUTH=true

# Google Sheets export — optional
GOOGLE_SHEETS_CREDENTIALS_JSON=
GOOGLE_SHEETS_CREDS=
GOOGLE_SHEET_ID=
```

**Important:**
- `SMTP_PASS` is an SMTP credential, **not** a normal account password.
- Set `SMTP_SECURE=true` for implicit TLS (commonly port 465).
- Set `SMTP_SECURE=false` and `SMTP_STARTTLS=true` for STARTTLS (commonly port 587).
- `SMTP_FROM_EMAIL` is the message sender.
- `RECIPIENT_EMAIL` is where the daily digest gets delivered (the job seeker)

For Railway, create a dedicated Google service account, enable the Google
Sheets API, share only the target spreadsheet with the service-account email as
Editor, and set the complete JSON key as the sealed
`GOOGLE_SHEETS_CREDENTIALS_JSON` variable. Do not commit it or copy a human
OAuth refresh token to Railway.

For local development, either put a service-account JSON file under the ignored
`.secrets/` directory and point `GOOGLE_SHEETS_CREDS` to it, or leave the path
blank and use Application Default Credentials. Only the Google Sheets scope is
required; Drive access is not used by the app.

---

## Step 4: Initialize Database (auto on first run)

Not needed manually — the database auto-initializes when you start the server. Tables created:
- `jobs`
- `companies`
- `outreach`
- `search_queries` (seeded with 6 default queries)
- `email_log`
- `api_usage`

---

## Step 5: Start the Server

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
Daily digest scheduler disabled
```

---

## Step 6: Open Dashboard

Open browser: **http://127.0.0.1:8000**

You'll see the Jobs page with 0 jobs.

---

## Step 7: First Run — Collect Jobs

Click **"Collect Jobs"** button (top right).

Wait 1-2 minutes. You should see ~500-1000 new jobs appear.

---

## Step 8: Generate Outreach

Navigate to **http://127.0.0.1:8000/outreach**

Click **"Find Contacts for Top Jobs"**. You'll see 15 outreach cards created.

---

## Step 9: Send Test Email

Click **"Send Email Now"** on the outreach page.

Check `RECIPIENT_EMAIL` inbox. Email should arrive in 10-30 seconds.

---

## Step 10: Let the Daily Schedule Run

After a successful manual email test, set `ENABLE_SCHEDULER=true` and restart.
The system then auto-runs every day at 9:00 AM IST:
1. Collects fresh jobs
2. Generates outreach for new top-scoring ones
3. Sends email

**Just keep the server running.** For 24/7 uptime, deploy to a small VPS (see below).

---

## Running on a Server (Optional)

To keep the daily schedule active, run on a VPS instead of your laptop.

### Option A: Railway

The included `railway.json` uses Railpack, one Uvicorn worker, and
`/health/ready`. Attach a persistent volume at `/data`, set the approved
variables individually, then deploy with `railway up`. Do not upload `.env`.

Railway blocks outbound SMTP on Free, Trial, and Hobby plans. SMTP requires
Pro or above followed by a redeploy; lower tiers need a transactional email
provider's HTTPS API. Leave `ENABLE_SCHEDULER=false` until a no-send connection
test succeeds and a recipient is explicitly configured.

### Option B: Keep your laptop on

If laptop is always on, leave the server running. Add to startup if needed.

---

## Troubleshooting

### "SMTP sender credentials are not configured"

- Check all required `SMTP_*` values
- Restart the server after editing `.env`

### "Authentication unsuccessful" when sending email

- Verify the provider's host, port, TLS mode, username, and SMTP password.
- For Gmail, use an App Password rather than the regular account password.

### Email lands in Spam folder

- First email from a new sender often does
- Tell recipient to mark as "Not Spam" once
- Future emails go to inbox

### JSearch returns 403 / 429

- Rate limit hit. Free tier = 200/month.
- Check usage: `http://127.0.0.1:8000/api/jsearch/status`
- Wait until next month or upgrade RapidAPI plan ($30/mo = 10,000 requests)

### No jobs appearing after "Collect Jobs"

- Check `.env` has `RAPIDAPI_KEY` (otherwise only free sources run)
- Score threshold is 25 — jobs below are dropped
- Check server logs for error messages
