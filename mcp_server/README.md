# Ridgeline Coffee MCP server

A small stdio MCP server that lets Claude answer questions about Ridgeline
Coffee directly — pending orders, low inventory, account lookups, roast
batches, subscriptions — by calling the Flask app's internal JSON API
(`app/api.py`), not the database file. That's the same pattern a real
internal MCP connector would use, and it means this server works unchanged
whether the app is running on localhost or deployed to Render.

## Setup

```bash
cd mcp_server
pip install -r requirements.txt
```

## Configure in Claude Desktop

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

To point at a deployed Render instance instead of localhost, change
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

- Auth is a single shared `X-API-Key` header — fine for a training demo,
  not a real auth scheme. Set `RIDGELINE_API_KEY` on both the Flask app
  and this server to the same value.
- The Flask app must be running (locally or on Render) for this server to
  answer anything — it's a thin client over the API, with no database
  access of its own.
