#!/usr/bin/env python3
"""
Run this once to authenticate with Whoop and save your tokens.
Usage: python3 auth.py
"""
import http.server
import threading
import webbrowser
import urllib.parse
import httpx
import json
import os
import sys
from pathlib import Path

CLIENT_ID = os.environ.get("WHOOP_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8888/callback"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
SCOPES = "read:recovery read:sleep read:workout read:cycles read:profile offline"
TOKEN_FILE = Path.home() / ".whoop_tokens.json"

auth_code = None
auth_event = threading.Event()


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                <h2>Authenticated successfully!</h2>
                <p>You can close this tab and return to the terminal.</p>
                </body></html>
            """)
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body>Error: {error}</body></html>".encode())

        auth_event.set()

    def log_message(self, format, *args):
        pass  # suppress server logs


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Set WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET environment variables.")
        print("\nGet credentials at: https://developer.whoop.com/")
        sys.exit(1)

    server = http.server.HTTPServer(("localhost", 8888), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()

    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    })
    url = f"{AUTH_URL}?{params}"

    print("Opening Whoop authorization page in your browser...")
    print(f"If it doesn't open, visit: {url}\n")
    webbrowser.open(url)

    auth_event.wait(timeout=120)
    server.server_close()

    if not auth_code:
        print("Error: No authorization code received (timed out).")
        sys.exit(1)

    print("Got authorization code. Exchanging for tokens...")

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
