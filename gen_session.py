"""
Run this ONCE locally to generate a Telethon StringSession.
The output string goes into your GitHub Secret as TG_SESSION.

Usage:
    pip install telethon
    python gen_session.py
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID   = int(input("Enter your api_id: ").strip())
API_HASH = input("Enter your api_hash: ").strip()

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n─── YOUR SESSION STRING (copy everything between the lines) ───")
    print(client.session.save())
    print("──────────────────────────────────────────────────────────────")
    print("\nPaste this as GitHub Secret: TG_SESSION")
