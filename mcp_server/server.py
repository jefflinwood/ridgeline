"""MCP server for Ridgeline Coffee Roasters.

Talks to the Flask app's internal JSON API (app/api.py) over HTTP rather
than touching the database directly — the same pattern a real internal
tool would use. Point it at a local dev server or the deployed Render URL
via RIDGELINE_API_BASE_URL.

Run:
    RIDGELINE_API_BASE_URL=http://127.0.0.1:5000/api \
    RIDGELINE_API_KEY=dev-api-key-change-me \
    python mcp_server/server.py

Then add it to Claude Desktop's config (see mcp_server/README.md).
"""
import os
from typing import Optional

import httpx

try:
    from mcp.server.fastmcp import FastMCP as _Server  # mcp < 2
except ModuleNotFoundError:
    from mcp.server.mcpserver import MCPServer as _Server  # mcp >= 2

API_BASE_URL = os.environ.get("RIDGELINE_API_BASE_URL", "http://127.0.0.1:5000/api")
API_KEY = os.environ.get("RIDGELINE_API_KEY", "dev-api-key-change-me")

server = _Server("ridgeline-coffee")


def _client():
    return httpx.Client(base_url=API_BASE_URL, headers={"X-API-Key": API_KEY}, timeout=10)


@server.tool()
def get_pending_orders(order_type: Optional[str] = None) -> list[dict]:
    """List orders that are not yet delivered or cancelled.

    Args:
        order_type: Optionally filter to "wholesale" or "retail".
    """
    with _client() as c:
        params = {"status": "pending"}
        if order_type:
            params["type"] = order_type
        resp = c.get("/orders", params=params)
        resp.raise_for_status()
        return resp.json()


@server.tool()
def get_order(order_number_or_id: str) -> dict:
    """Get full detail (including line items) for one order by its numeric id."""
    with _client() as c:
        resp = c.get(f"/orders/{order_number_or_id}")
        resp.raise_for_status()
        return resp.json()


@server.tool()
def update_order_status(order_id: int, status: str) -> dict:
    """Update an order's status.

    Args:
        order_id: Numeric order id (see get_pending_orders for ids).
        status: One of pending, confirmed, roasting, shipped, delivered, cancelled.
    """
    with _client() as c:
        resp = c.post(f"/orders/{order_id}/status", json={"status": status})
        resp.raise_for_status()
        return resp.json()


@server.tool()
def get_shipping_plan(method: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
    """List parcel shipments or delivery-truck loads with destinations and capacity.

    Args:
        method: Optionally filter to ups, fedex, usps, or delivery_truck.
        status: Optionally filter to planned, ready, in_transit, delivered, or exception.
    """
    with _client() as c:
        params = {}
        if method:
            params["method"] = method
        if status:
            params["status"] = status
        resp = c.get("/shipments", params=params)
        resp.raise_for_status()
        return resp.json()


@server.tool()
def get_low_stock() -> dict:
    """Return green coffee lots running low (<=15% of what arrived) and
    roasted products with fewer than 5 cases in stock."""
    with _client() as c:
        lots = c.get("/inventory/low")
        lots.raise_for_status()
        products = c.get("/products")
        products.raise_for_status()
        low_products = [p for p in products.json() if p["cases_in_stock"] < 5]
        return {"low_green_coffee_lots": lots.json(), "low_roasted_products": low_products}


@server.tool()
def get_account_summary(name: str) -> list[dict]:
    """Look up a wholesale or retail account by (partial) name and return
    its contact info, open order count, and orders/subscriptions.

    Args:
        name: Full or partial account name, e.g. "Northside" or "Smith".
    """
    with _client() as c:
        resp = c.get("/accounts")
        resp.raise_for_status()
        matches = [a for a in resp.json() if name.lower() in a["name"].lower()]
        results = []
        for m in matches:
            detail = c.get(f"/accounts/{m['id']}")
            detail.raise_for_status()
            results.append(detail.json())
        return results


@server.tool()
def get_recent_roast_batches(limit: int = 10) -> list[dict]:
    """Return the most recent roast batches, most recent first."""
    with _client() as c:
        resp = c.get("/roast-batches", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()


@server.tool()
def search_products(query: Optional[str] = None) -> list[dict]:
    """List roasted product SKUs, optionally filtered by a name/origin/roast substring."""
    with _client() as c:
        resp = c.get("/products")
        resp.raise_for_status()
        products = resp.json()
        if query:
            q = query.lower()
            products = [
                p for p in products
                if q in p["name"].lower() or q in p["origin"].lower() or q in p["roast_level"].lower()
            ]
        return products


@server.tool()
def get_subscriptions(status: Optional[str] = None) -> list[dict]:
    """List subscriptions, optionally filtered by status (active, paused, cancelled)."""
    with _client() as c:
        resp = c.get("/subscriptions", params={"status": status} if status else {})
        resp.raise_for_status()
        return resp.json()


@server.tool()
def pause_subscription(subscription_id: int) -> dict:
    """Pause a customer's subscription by its id."""
    with _client() as c:
        resp = c.post(f"/subscriptions/{subscription_id}/pause")
        resp.raise_for_status()
        return resp.json()


@server.tool()
def resume_subscription(subscription_id: int) -> dict:
    """Resume a paused subscription by its id."""
    with _client() as c:
        resp = c.post(f"/subscriptions/{subscription_id}/resume")
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    server.run(transport="stdio")
