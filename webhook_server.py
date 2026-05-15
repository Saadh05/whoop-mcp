#!/usr/bin/env python3
"""
Whoop webhook server — receives real-time events from Whoop.
Run this on a machine with a public URL (or use ngrok for local dev).

Usage:
  WHOOP_CLIENT_SECRET=your_secret .venv/bin/python webhook_server.py

Whoop will POST events to: http://your-host:8080/webhook
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("whoop-webhook")

CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "")

# Whoop event types
EVENT_TYPES = {
    "workout.updated",
    "sleep.updated",
    "recovery.updated",
    "body_measurement.updated",
}


def verify_signature(body: bytes, signature_header: str) -> bool:
    """Verify the HMAC-SHA256 signature Whoop sends with every request."""
    if not CLIENT_SECRET or not signature_header:
        return False
    expected = hmac.new(
        CLIENT_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


async def handle_webhook(request: Request) -> PlainTextResponse:
    body = await request.body()
    signature = request.headers.get("x-whoop-signature", "")

    if not verify_signature(body, signature):
        log.warning("Invalid signature — rejecting request")
        return PlainTextResponse("Unauthorized", status_code=401)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return PlainTextResponse("Bad Request", status_code=400)

    event_type = payload.get("type")
    user_id = payload.get("user_id")
    timestamp = datetime.utcnow().isoformat()

    log.info(f"[{timestamp}] Event: {event_type} | User: {user_id}")

    if event_type not in EVENT_TYPES:
        log.warning(f"Unknown event type: {event_type}")
        return PlainTextResponse("OK", status_code=200)

    # Dispatch to the appropriate handler
    handlers = {
        "workout.updated": on_workout_updated,
        "sleep.updated": on_sleep_updated,
        "recovery.updated": on_recovery_updated,
        "body_measurement.updated": on_body_measurement_updated,
    }
    handler = handlers.get(event_type)
    if handler:
        await handler(payload)

    # Whoop requires a 200 response quickly — do heavy work async if needed
    return PlainTextResponse("OK", status_code=200)


async def handle_health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ── Event handlers ────────────────────────────────────────────────────────────
# Add your logic here — write to a file, database, notify, etc.

async def on_workout_updated(payload: dict):
    data = payload.get("data", {})
    log.info(f"  Workout updated: id={data.get('id')} sport={data.get('sport_id')}")


async def on_sleep_updated(payload: dict):
    data = payload.get("data", {})
    log.info(f"  Sleep updated: id={data.get('id')}")


async def on_recovery_updated(payload: dict):
    data = payload.get("data", {})
    score = (data.get("score") or {}).get("recovery_score")
    log.info(f"  Recovery updated: id={data.get('id')} score={score}%")


async def on_body_measurement_updated(payload: dict):
    log.info("  Body measurement updated")


# ── App ───────────────────────────────────────────────────────────────────────

app = Starlette(routes=[
    Route("/webhook", handle_webhook, methods=["POST"]),
    Route("/health", handle_health, methods=["GET"]),
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    log.info(f"Starting Whoop webhook server on port {port}")
    log.info("Webhook URL to register: http://<your-host>:{port}/webhook")
    uvicorn.run(app, host="0.0.0.0", port=port)
