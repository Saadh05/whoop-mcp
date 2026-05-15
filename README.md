# whoop-mcp

A Model Context Protocol (MCP) server that connects your Whoop fitness data to Claude. Ask natural language questions about your recovery, sleep, workouts, and more.

## Available Tools

| Tool | Description |
|---|---|
| `get_profile` | Your name and email |
| `get_body_measurement` | Height, weight, max heart rate |
| `get_recovery` | Recovery %, HRV, resting heart rate |
| `get_sleep` | Duration, efficiency, sleep stages |
| `get_workouts` | Strain, calories, sport type |
| `get_cycles` | Daily strain and total calories burned |

All data tools accept optional `start` and `end` parameters (ISO 8601 format) and default to the last 30 days.

## Setup

### 1. Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install dependencies

```bash
cd whoop-mcp
uv venv --python 3.12
uv pip install mcp httpx
```

### 3. Get Whoop API credentials

1. Go to [https://developer.whoop.com/](https://developer.whoop.com/)
2. Create a new app and fill in the required fields:
   - **Privacy Policy URL** — host `privacy.html` on GitHub Pages (see below) and paste that URL
   - **Webhook URL** — optional; set to `http://your-host:8080/webhook` if running `webhook_server.py`
   - **Redirect URI** — `http://localhost:8888/callback`
3. Copy your **Client ID** and **Client Secret**

### 4. Authenticate (one time)

```bash
WHOOP_CLIENT_ID=your_id WHOOP_CLIENT_SECRET=your_secret .venv/bin/python auth.py
```

This opens a browser, you approve access, and tokens are saved to `~/.whoop_tokens.json`.

### 5. Add to Claude Code

Add this to your `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "/absolute/path/to/whoop-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/whoop-mcp/server.py"],
      "env": {
        "WHOOP_CLIENT_ID": "your_client_id",
        "WHOOP_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

Restart Claude Code and the server will load automatically.

## Example Questions

- "What was my average HRV last week?"
- "How many hours of sleep did I average this month?"
- "Show me my recovery trend over the past 30 days"
- "Which workouts had the highest strain scores?"
- "Compare my sleep efficiency between weekdays and weekends"

## Privacy Policy

`privacy.html` is a ready-to-host privacy policy page required by the Whoop developer portal.

**Host it on GitHub Pages:**
1. Push this repo to GitHub
2. Go to **Settings → Pages → Source → main branch**
3. Your privacy policy URL will be: `https://your-username.github.io/whoop-mcp/privacy.html`

## Webhooks (optional)

`webhook_server.py` receives real-time events from Whoop (new workout, sleep, recovery, body measurement).

```bash
WHOOP_CLIENT_SECRET=your_secret .venv/bin/python webhook_server.py
```

For local development, expose it with [ngrok](https://ngrok.com/):

```bash
ngrok http 8080
# Then register https://xxxx.ngrok-free.app/webhook in the Whoop developer portal
```

Supported events: `workout.updated`, `sleep.updated`, `recovery.updated`, `body_measurement.updated`

## Project Structure

```
whoop-mcp/
├── server.py            # MCP server — tools Claude calls
├── whoop_client.py      # Whoop API client with token refresh
├── auth.py              # One-time OAuth setup script
├── webhook_server.py    # Real-time Whoop event receiver
├── privacy.html         # Privacy policy (host on GitHub Pages)
└── requirements.txt     # Python dependencies
```
