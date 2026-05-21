"""Obtain a Google OAuth refresh token for the Calendar API.

Run this locally **once** to get a refresh token that the GitHub Actions
workflow can use. Place ``client_secret.json`` (downloaded from Google
Cloud Console as a Desktop application OAuth client) in the same
directory and run::

    python scripts/get_refresh_token.py

A browser window will open for you to consent. The resulting
``GOOGLE_CLIENT_ID``, ``GOOGLE_CLIENT_SECRET`` and ``GOOGLE_REFRESH_TOKEN``
values will be printed to the terminal — register them as GitHub Actions
secrets.
"""

from __future__ import annotations

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CLIENT_SECRET_FILE = "client_secret.json"


def main() -> None:
    secret_path = Path(CLIENT_SECRET_FILE)
    if not secret_path.exists():
        print(
            f"ERROR: {CLIENT_SECRET_FILE} not found in the current directory.\n"
            "Download a Desktop application OAuth client JSON from Google Cloud "
            "Console and save it as 'client_secret.json' next to this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh_token is issued
    # even if the user has previously authorised this client.
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    if not credentials.refresh_token:
        print(
            "ERROR: No refresh token was returned. Revoke previous access at "
            "https://myaccount.google.com/permissions and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print("=" * 60)
    print("Register the following values as GitHub Actions secrets:")
    print("=" * 60)
    print(f"GOOGLE_CLIENT_ID      = {credentials.client_id}")
    print(f"GOOGLE_CLIENT_SECRET  = {credentials.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN  = {credentials.refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
