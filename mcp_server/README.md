# Ridgeline Coffee MCP server

A small MCP server that lets Claude answer questions about Ridgeline
Coffee directly — pending orders, low inventory, account lookups, roast
batches, subscriptions — by calling the Flask app's internal JSON API
(`app/api.py`), not the database file. That's the same pattern a real
internal MCP connector would use. It supports both local stdio and hosted
Streamable HTTP transports.

## Connect to the hosted server

The Render deployment exposes the MCP endpoint alongside the website:

```text
https://<your-render-app>.onrender.com/mcp
```

Use that URL in any MCP client that supports remote Streamable HTTP servers.
No local Python process or API key is required by the client. The MCP OAuth
flow opens a Ridgeline page where the participant enters the class password.

Render generates `MCP_CLASS_PASSWORD` on the first Blueprint deployment. Copy
its value from the service's Environment page and share it with the class. The
MCP endpoint returns `401` until the client completes OAuth; authorization
codes expire after five minutes and access tokens after eight hours.

To serve a custom domain, set `MCP_PUBLIC_BASE_URL` to its HTTPS origin and add
its host to the comma-separated `MCP_ALLOWED_HOSTS` environment variable.
Browser-based MCP clients also need their origins in `MCP_ALLOWED_ORIGINS`.

## Setup

```bash
cd mcp_server
pip install -r requirements.txt
```

## Configure a local stdio server

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ridgeline-coffee": {
      "command": "python3",
      "args": ["/absolute/path/to/ridgeline/mcp_server/server.py"],
      "env": {
        "RIDGELINE_API_BASE_URL": "http://127.0.0.1:5000/api",
        "RIDGELINE_API_KEY": "dev-api-key-change-me"
      }
    }
  }
}
```

To run the stdio process against a deployed Render instance instead of
localhost, change
`RIDGELINE_API_BASE_URL` to `https://<your-render-app>.onrender.com/api`
and set `RIDGELINE_API_KEY` to match whatever you set as the
`RIDGELINE_API_KEY` environment variable on Render.

## Tools

| Tool | What it does |
|---|---|
| `get_pending_orders` | Orders not yet delivered/cancelled, optionally by type |
| `get_order` | Full detail + line items for one order |
| `update_order_status` | Move an order to a new status (write) |
| `update_order_due_date` | Set an order's delivery deadline (write) |
| `get_shipping_plan` | Parcel shipments and truck loads, optionally by method/status |
| `get_low_stock` | Green coffee lots and roasted products running low |
| `get_account_summary` | Look up an account by name — contact, orders, subscriptions |
| `get_recent_roast_batches` | Most recent roast batches |
| `search_products` | Product catalog, filterable by name/origin/roast |
| `get_subscriptions` | List subscriptions, optionally by status |
| `pause_subscription` / `resume_subscription` | Manage a subscription (write) |

## Notes

- The hosted transport uses MCP-native OAuth 2.1 with dynamic client
  registration, PKCE, bearer tokens, and the `MCP_CLASS_PASSWORD` sign-in.
  The internal `/api/*` calls use the separate `RIDGELINE_API_KEY`; that key
  is never sent to MCP clients.
- The Flask app must be running for the stdio server to answer anything —
  it's a thin client over the API, with no database access of its own.
- On Render, `web.py` serves Flask and MCP from one ASGI process. The MCP
  endpoint calls the Flask API over the service's local HTTP port.
- OAuth registrations and tokens are intentionally held in memory for this
  classroom demo. Keep one Uvicorn worker; a restart asks clients to connect
  again.
