#!/usr/bin/env python3
"""
Live unlock code viewer for FRZR BURN testing.

Usage:
    uv run python test_codes.py

Shows the current 10-digit keypad code for every active student.
Refreshes every second with a countdown until the TOTP rotates (every 30s).
"""
import asyncio
import os
import sys
import time

import asyncpg
import pyotp
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

TOTP_KEY = os.getenv("TOTP_ENCRYPTION_KEY", "").strip("\"'")
DB_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg", "postgresql")


def decrypt_secret(encrypted: str) -> str:
    return Fernet(TOTP_KEY.encode()).decrypt(encrypted.encode()).decode()


async def fetch_students() -> list:
    ssl = "require" if "supabase" in DB_URL else None
    conn = await asyncpg.connect(DB_URL, ssl=ssl)
    rows = await conn.fetch(
        "SELECT member_id, full_name, totp_secret_encrypted "
        "FROM students WHERE active = true ORDER BY member_id"
    )
    await conn.close()
    return rows


TOTP_INTERVAL = 60  # must match security.py


def render(students: list) -> None:
    remaining = TOTP_INTERVAL - (int(time.time()) % TOTP_INTERVAL)
    filled = int(remaining / TOTP_INTERVAL * 30)
    bar = "█" * filled + "░" * (30 - filled)

    print("\033[2J\033[H", end="")  # clear screen, move cursor to top
    print("┌─────────────────────────────────────────┐")
    print("│       FRZR BURN  —  Live Test Codes     │")
    print(f"│  Rotates in {remaining:2d}s  {bar} │")
    print("├─────────────────────────────────────────┤")

    for s in students:
        try:
            secret = decrypt_secret(s["totp_secret_encrypted"])
            code = s["member_id"] + pyotp.TOTP(secret, interval=TOTP_INTERVAL).now()
            name = s["full_name"][:22]
            print(f"│  {name:<22}                  │")
            print(f"│  ▶  Type on keypad:  {code}  ◀      │")
            print("│                                         │")
        except Exception as e:
            print(f"│  {s['member_id']}: DECRYPT ERROR — {e}  │")

    print("└─────────────────────────────────────────┘")
    print("  Ctrl+C to quit")


async def main() -> None:
    if not TOTP_KEY:
        print("ERROR: TOTP_ENCRYPTION_KEY not found in .env")
        sys.exit(1)

    print("Connecting to database…")
    try:
        students = await fetch_students()
    except Exception as e:
        print(f"ERROR: Could not connect to DB — {e}")
        sys.exit(1)

    if not students:
        print("No active students in DB. Insert a student first.")
        sys.exit(0)

    try:
        while True:
            render(students)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDone.")


asyncio.run(main())
