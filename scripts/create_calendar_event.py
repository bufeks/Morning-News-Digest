"""Create a Google Calendar event from digest.json.

Reads ``digest.json`` (produced by Claude Code), exchanges the configured
OAuth refresh token for an access token, then inserts a 7:00–7:30 JST
event into the user's Google Calendar with the digest HTML as the body.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
JST = timezone(timedelta(hours=9))


def fail(message: str) -> "None":
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        fail(
            f"Required environment variable '{name}' is not set. "
            "Configure it as a GitHub Actions secret."
        )
    return value


def load_description_html() -> str:
    digest_path = Path("digest.json")
    if not digest_path.exists():
        fail("digest.json not found. Did the Claude Code step run successfully?")

    try:
        data = json.loads(digest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"digest.json is not valid JSON: {exc}")

    if not isinstance(data, dict):
        fail("digest.json must be a JSON object.")

    html = data.get("description_html")
    if not isinstance(html, str) or not html.strip():
        fail("digest.json is missing a non-empty 'description_html' string.")
    return html


def fetch_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if response.status_code != 200:
        fail(
            "Failed to exchange refresh token for access token "
            f"(HTTP {response.status_code}): {response.text}"
        )

    payload = response.json()
    token = payload.get("access_token")
    if not token:
        fail(f"Token endpoint did not return an access_token: {payload}")
    return token


def build_event(description_html: str) -> dict:
    now_jst = datetime.now(JST)
    start = now_jst.replace(hour=7, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=30)

    title = f"☕ 今朝のニュースまとめ（{start.month}/{start.day}）"

    return {
        "summary": title,
        "description": description_html,
        "start": {
            "dateTime": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "dateTime": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "Asia/Tokyo",
        },
    }


def insert_event(calendar_id: str, access_token: str, event: dict) -> dict:
    url = f"{CALENDAR_API_BASE}/calendars/{calendar_id}/events"
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        data=json.dumps(event, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    )
    if response.status_code not in (200, 201):
        fail(
            "Failed to create calendar event "
            f"(HTTP {response.status_code}): {response.text}"
        )
    return response.json()


def main() -> None:
    client_id = require_env("GOOGLE_CLIENT_ID")
    client_secret = require_env("GOOGLE_CLIENT_SECRET")
    refresh_token = require_env("GOOGLE_REFRESH_TOKEN")
    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID") or "primary"

    description_html = load_description_html()
    access_token = fetch_access_token(client_id, client_secret, refresh_token)
    event = build_event(description_html)
    created = insert_event(calendar_id, access_token, event)

    html_link = created.get("htmlLink", "(no htmlLink returned)")
    print(f"Created calendar event: {html_link}")


if __name__ == "__main__":
    main()
