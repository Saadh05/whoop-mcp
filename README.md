# whoop-mcp

A Model Context Protocol (MCP) server that connects your Whoop fitness data to Claude. Ask natural language questions about your recovery, sleep, workouts, and more — directly in Claude chat.

## What You Can Ask

- *"What was my recovery score today?"*
- *"How did I sleep this week?"*
- *"Show me my HRV trend over the last 30 days"*
- *"Which workouts had the highest strain?"*
- *"Compare my sleep efficiency this month"*

## Available Tools

| Tool | Description |
|---|---|
| `get_profile` | Your name and email |
| `get_body_measurement` | Height, weight, max heart rate |
| `get_recovery` | Recovery %, HRV, resting heart rate, SpO2 |
| `get_sleep` | Duration, efficiency, sleep stages, disturbances |
| `get_workouts` | Strain, calories, sport type |
| `get_cycles` | Daily strain and total calories burned |

All data tools accept optional `start` and `end` date parameters and default to the last 30 days.

---

## Setup

### 1. Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone this repo to a path **without spaces**:

```bash
git clone https://github.com/your-username/whoop-mcp.git ~/whoop-mcp
cd ~/whoop-mcp
```

Install dependencies:

```bash
uv venv --python 3.12
uv pip install mcp httpx
```

### 2. Get Whoop API credentials

1. Go to [https://developer.whoop.com/](https://developer.whoop.com/)
2. Create a new app and fill in:
   - **Redirect URI**: `http://localhost:8888/callback`
   - **Privacy Policy URL**: your GitHub Pages URL (see [Privacy Policy](#privacy-policy) below)
3. Copy your **Client ID** and **Client Secret**

### 3. Authenticate (one time only)

```bash
WHOOP_CLIENT_ID=your_client_id \
WHOOP_CLIENT_SECRET=your_client_secret \
.venv/bin/python auth.py
```

This opens the Whoop authorization page in your browser. After you approve:
- Your browser will show an error on `localhost:8888` — that's expected
- Copy the full URL from the address bar and paste it into the terminal
- Tokens are saved to `~/.whoop_tokens.json`

You will **not** need to do this again. The server automatically refreshes your token.

### 4. Configure the Claude Desktop App

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and add:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "/Users/your-username/whoop-mcp/.venv/bin/python",
      "args": ["/Users/your-username/whoop-mcp/server.py"],
      "env": {
        "WHOOP_CLIENT_ID": "your_client_id",
        "WHOOP_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

> **Important:** The path to `whoop-mcp` must not contain spaces — this is why step 1 clones to `~/whoop-mcp`.

### 5. Restart Claude

Fully quit Claude (Cmd+Q) and reopen it. The Whoop server should show as connected under **Settings → Developer**.

---

## Privacy Policy

`privacy.html` is a ready-to-host privacy policy page required by the Whoop developer portal.

**Host it on GitHub Pages:**
1. Push this repo to GitHub
2. Go to **Settings → Pages → Source → Deploy from a branch → main / root**
3. Your privacy policy URL will be:
   ```
   https://your-username.github.io/whoop-mcp/privacy.html
   ```

---

## Webhooks (optional)

`webhook_server.py` receives real-time events from Whoop when new data is recorded.

```bash
WHOOP_CLIENT_SECRET=your_client_secret .venv/bin/python webhook_server.py
```

For local development, expose it with [ngrok](https://ngrok.com/):

```bash
ngrok http 8080
# Register the https URL in the Whoop developer portal
```

Supported events: `workout.updated`, `sleep.updated`, `recovery.updated`, `body_measurement.updated`

---

## Project Structure

```
whoop-mcp/
├── server.py            # MCP server — tools Claude calls
├── whoop_client.py      # Whoop API v2 client with auto token refresh
├── auth.py              # One-time OAuth setup script
├── webhook_server.py    # Real-time Whoop event receiver (optional)
├── privacy.html         # Privacy policy page for GitHub Pages
└── requirements.txt     # Python dependencies (mcp, httpx)
```

## Notes

- Tokens are stored at `~/.whoop_tokens.json` and auto-refreshed — you never need to re-run `auth.py` unless you revoke access from the Whoop app
- Uses the Whoop API v2
- Tested on macOS with Python 3.12
