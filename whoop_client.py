import json
import os
from pathlib import Path
from typing import Any
import httpx

API_BASE = "https://api.prod.whoop.com/developer/v2"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
TOKEN_FILE = Path.home() / ".whoop_tokens.json"


def _normalize_dt(dt: str) -> str:
    """Ensure a date/datetime string is full RFC 3339 format Whoop requires.
    '2026-05-10' -> '2026-05-10T00:00:00.000Z'
    Already-full strings are passed through unchanged.
    """
    if not dt:
        return dt
    if "T" not in dt:
        return f"{dt}T00:00:00.000Z"
    if not dt.endswith("Z") and "+" not in dt:
        return f"{dt}Z"
    return dt


class WhoopClient:
    def __init__(self):
        self.client_id = os.environ.get("WHOOP_CLIENT_ID", "")
        self.client_secret = os.environ.get("WHOOP_CLIENT_SECRET", "")
        self._tokens: dict = {}
        self._load_tokens()

    def _load_tokens(self):
        if TOKEN_FILE.exists():
            self._tokens = json.loads(TOKEN_FILE.read_text())

    def _save_tokens(self):
        TOKEN_FILE.write_text(json.dumps(self._tokens, indent=2))
        TOKEN_FILE.chmod(0o600)

    def _refresh_access_token(self):
        refresh_token = self._tokens.get("refresh_token")
        if not refresh_token:
            raise RuntimeError("No refresh token found. Run auth.py to authenticate.")

        resp = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        resp.raise_for_status()
        self._tokens.update(resp.json())
        self._save_tokens()

    def _get(self, path: str, params: dict | None = None) -> Any:
        if not self._tokens:
            raise RuntimeError("Not authenticated. Run auth.py first.")

        def attempt(retry=True):
            token = self._tokens.get("access_token")
            resp = httpx.get(
                f"{API_BASE}{path}",
                headers={"Authorization": f"Bearer {token}"},
                params=params or {},
            )
            if resp.status_code == 401 and retry:
                self._refresh_access_token()
                return attempt(retry=False)
            resp.raise_for_status()
            return resp.json()

        return attempt()

    def _paginate(self, path: str, params: dict | None = None) -> list:
        params = params or {}
        results = []
        while True:
            data = self._get(path, params)
            records = data.get("records", [])
            results.extend(records)
            next_token = data.get("next_token")
            if not next_token:
                break
            params["nextToken"] = next_token
        return results

    def get_profile(self) -> dict:
        return self._get("/user/profile/basic")

    def get_body_measurement(self) -> dict:
        return self._get("/user/measurement/body")

    def _date_params(self, start: str | None, end: str | None) -> dict:
        params = {}
        if start:
            params["start"] = _normalize_dt(start)
        if end:
            params["end"] = _normalize_dt(end)
        return params

    def get_cycles(self, start: str | None = None, end: str | None = None) -> list:
        """Fetch physiological cycles (includes recovery score embedded)."""
        return self._paginate("/cycle", self._date_params(start, end))

    def get_recovery(self, start: str | None = None, end: str | None = None) -> list:
        """Fetch recovery records from the dedicated /recovery list endpoint."""
        return self._paginate("/recovery", self._date_params(start, end))

    def get_sleep(self, start: str | None = None, end: str | None = None) -> list:
        return self._paginate("/activity/sleep", self._date_params(start, end))

    def get_workouts(self, start: str | None = None, end: str | None = None) -> list:
        return self._paginate("/activity/workout", self._date_params(start, end))
