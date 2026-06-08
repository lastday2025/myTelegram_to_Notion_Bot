# Telegram → Notion Job Clipper (GitHub Actions)

Polls a Telegram channel every 2 hours and saves new job listings to Notion.
No server required. Runs entirely on GitHub Actions free tier.

---

## Setup (one-time, ~10 minutes)

### 1. Get Telegram API credentials
1. Go to https://my.telegram.org
2. Log in → "API development tools"
3. Create an app — copy `api_id` and `api_hash`

### 2. Generate a session string (run locally once)
```bash
pip install telethon
python gen_session.py
```
Copy the long string it prints — this is your `TG_SESSION`.

### 3. Find your channel identifier
- Public channel: just the username, e.g. `jobschannel`
- Private channel: the numeric ID, e.g. `-1001234567890`
  - To get a private channel ID: forward a message from it to @userinfobot

### 4. Create a GitHub repo
- Push this folder to a new GitHub repo (can be private)
- Create the file `last_message_id.txt` with content `0` in the root

### 5. Add GitHub Secrets
Go to repo → Settings → Secrets and variables → Actions → New repository secret

| Secret name        | Value                        |
|--------------------|------------------------------|
| `TG_API_ID`        | your api_id (number)         |
| `TG_API_HASH`      | your api_hash                |
| `TG_SESSION`       | output of gen_session.py     |
| `TG_CHANNEL`       | channel username or ID       |
| `NOTION_TOKEN`     | your Notion integration token|
| `NOTION_DATABASE_ID` | your Notion database ID    |

### 6. Done
The workflow runs every 2 hours automatically.
You can also trigger it manually: Actions tab → "Telegram → Notion Job Clipper" → Run workflow.

---

## Notion database columns expected

| Column     | Type      |
|------------|-----------|
| Company    | Title     |
| Role       | Rich text |
| Location   | Rich text |
| Status     | Status    |

If you want the `Category` column back (BE/PM/AE/Other), you can add it
manually in Notion and update `bot.py` to include it in the payload.

---

## Changing the schedule

Edit `.github/workflows/clipper.yml`, line:
```yaml
- cron: "0 */2 * * *"   # every 2 hours
```
Examples:
- Every hour: `"0 * * * *"`
- Every 4 hours: `"0 */4 * * *"`
- Twice a day: `"0 9,18 * * *"`
