"""
Telegram → Notion Job Clipper (polling mode)
Runs on a schedule (GitHub Actions cron), fetches new messages
from a Telegram channel/group, and saves each job to Notion.
"""

import os
import json
import asyncio
import re
from pathlib import Path
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import requests

# ── CONFIG (all pulled from environment variables / GitHub Secrets) ────────
API_ID        = int(os.environ["TG_API_ID"])
API_HASH      = os.environ["TG_API_HASH"]
SESSION_STR   = os.environ["TG_SESSION"]          # generated once via gen_session.py
CHANNEL       = os.environ["TG_CHANNEL"]          # e.g. "jobschannel" or "-1001234567890"
NOTION_TOKEN  = os.environ["NOTION_TOKEN"]
DATABASE_ID   = os.environ["NOTION_DATABASE_ID"]

# File that tracks the last message ID we processed.
# GitHub Actions commits this back to the repo after each run.
STATE_FILE    = Path("last_message_id.txt")

NOTION_VERSION = "2022-06-28"
NOTION_URL     = "https://api.notion.com/v1/pages"

# ── STATE: last seen message ID ────────────────────────────────────────────
def load_last_id() -> int:
    if STATE_FILE.exists():
        try:
            return int(STATE_FILE.read_text().strip())
        except ValueError:
            pass
    return 0

def save_last_id(msg_id: int):
    STATE_FILE.write_text(str(msg_id))

# ── PARSING ────────────────────────────────────────────────────────────────
def parse_jobs(full_text: str) -> list[str]:
    """Split a multi-listing message into individual job blocks."""
    parts = re.split(r'\n(?=\d+\)\s*Company\s*[-–])', full_text, flags=re.IGNORECASE)
    jobs  = [p.strip() for p in parts if re.match(r'^\d+\)\s*Company\s*[-–]', p.strip(), re.IGNORECASE)]
    return jobs if jobs else [full_text.strip()]

def extract_field(text: str, field: str) -> str:
    """Extract a field like 'Role - Senior Engineer' from text."""
    match = re.search(rf'^{field}\s*[-–]\s*(.+)', text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""

def build_title(job_text: str) -> str:
    first_line = next((l for l in job_text.splitlines() if l.strip()), job_text)
    return re.sub(r'^\d+\)\s*(Company\s*[-–]\s*)?', '', first_line, flags=re.IGNORECASE).strip()[:90] or "(no text)"

def chunk_text(text: str, size: int = 1900) -> list[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

# ── NOTION ─────────────────────────────────────────────────────────────────
def save_to_notion(job_text: str) -> bool:
    title    = build_title(job_text)
    role     = extract_field(job_text, "Role")
    location = extract_field(job_text, "Location")

    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        }
        for chunk in chunk_text(job_text)
    ]

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Company":  {"title":     [{"text": {"content": title}}]},
            "Status":   {"status":    {"name": "To review"}},
            "Role":     {"rich_text": [{"text": {"content": role}}]},
            "Location": {"rich_text": [{"text": {"content": location}}]},
        },
        "children": children,
    }

    headers = {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": NOTION_VERSION,
    }

    resp = requests.post(NOTION_URL, headers=headers, json=payload, timeout=15)
    if resp.status_code == 200:
        print(f"  ✓ Saved: {title}")
        return True
    else:
        print(f"  ✗ Failed ({resp.status_code}): {title}\n    {resp.text[:200]}")
        return False

# ── MAIN ───────────────────────────────────────────────────────────────────
async def main():
    last_id  = load_last_id()
    new_last = last_id
    total    = 0
    saved    = 0

    print(f"Fetching messages after ID {last_id} from '{CHANNEL}' ...")

    async with TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH) as client:
        async for message in client.iter_messages(CHANNEL, min_id=last_id, reverse=True):
            if not message.text:
                continue

            text = message.text.strip()
            if not text:
                continue

            print(f"\nMessage {message.id}:")
            jobs = parse_jobs(text)

            for job in jobs:
                total += 1
                ok = save_to_notion(job)
                if ok:
                    saved += 1

            if message.id > new_last:
                new_last = message.id

    if new_last > last_id:
        save_last_id(new_last)
        print(f"\nUpdated last_message_id → {new_last}")

    print(f"\nDone. {saved}/{total} jobs saved to Notion.")

if __name__ == "__main__":
    asyncio.run(main())
