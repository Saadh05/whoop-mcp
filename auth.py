#!/usr/bin/env python3
"""
Run this once to authenticate with Whoop and save your tokens.
Usage: python3 auth.py
"""
import webbrowser
import urllib.parse
import httpx
import json
import os
import sys
import secrets
from pathlib import Path

CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8888/callback"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
SCOPES = "read:recovery read:sleep read:workout read:cycles read:profile offline"
TOKEN_FILE = Path.home() / ".whoop_tokens.json"


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET environment variables.")
        print("\nGet credentials at: https://developer.whoop.com/")
        sys.exit(1)

    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    })
    url = f"{AUTH_URL}?{params}"

    print("Opening Whoop authorization page in your browser...")
    print(f"\nIf it doesn't open automatically, visit:\n{url}\n")
    webbrowser.open(url)

    print("After you click 'Authorize' on the WHOOP page, your browser will")
    print("try to load localhost:8888 and show an error — that's expected.")
    print("\nCopy the full URL from your browser's address bar and paste it here:")
    redirect_url = input("> ").strip()

    parsed = urllib.parse.urlparse(redirect_url)
    params_back = urllib.parse.parse_qs(parsed.query)

    if "error" in params_back:
        print(f"Error from WHOOP: {params_back['error'][0]}")
        sys.exit(1)

    if "code" not in params_back:
        print("No authorization code found in that URL. Make sure you copied the full URL.")
        sys.exit(1)

    returned_state = params_back.get("state", [None])[0]
    if returned_state != state:
        print("Warning: state mismatch — continuing anyway.")

    auth_code = params_back["code"][0]
    print("\nGot authorization code. Exchanging for tokens...")

    resp = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    resp.raise_for_status()
    tokens = resp.json()

    TOKEN_FILE.write_text(json.dumps(tokens, indent=2))
    TOKEN_FILE.chmod(0o600)
    print(f"Tokens saved to {TOKEN_FILE}")
    print("\nSetup complete! You can now use the Whoop MCP server.")


if __name__ == "__main__":
    main()
