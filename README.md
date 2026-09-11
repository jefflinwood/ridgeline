# Ridgeline Coffee

A small Flask web app for **Ridgeline Coffee Roasters** — a coffee roaster with
wholesale accounts (cafes, offices, hotel groups buying by the case) and retail
subscribers (buying bagged coffee, some on a recurring subscription).

Built as a **demo backend**: it exists to give the Claude Desktop + Cowork
training class real data to point Excel, SQL, and Outlook demos at — an
orders/inventory system with roles, a database, and workflows that behave
like a real small-business app.

## What's in it

- **Auth & roles** — `admin`, `staff` (roastery ops), and `customer`
  (wholesale account contacts and retail subscribers), via Flask-Login.
- **Green coffee inventory** — lots of unroasted coffee, flagged low when
  under 15% of what arrived.
- **Roast log** — log a batch against a lot; it deducts green weight from
  the lot and adds finished bags to product stock.
- **Orders** — wholesale (by the case) and retail (by the bag), with status
  tracking (`pending` → `confirmed` → `roasting` → `shipped` → `delivered`)
  and explicit customer delivery due dates.
- **Shipping** — UPS, FedEx, USPS, and capacity-planned delivery-truck loads
  to customer warehouses, with local, in-state, and interstate carriers.
- **Subscriptions** — recurring retail orders with pause/resume/cancel.
- **Accounts** — wholesale and retail customer records, including a couple
  of non-US accounts (Toronto, London) if you want an FX angle later.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python seed.py                  # creates ridgeline.db and loads demo data
python run.py                   # http://127.0.0.1:5000
```

`seed.py` drops and recreates all tables, so re-run it any time you want to
reset to a clean demo state. (The app also auto-creates and seeds an empty
database on first boot — see "Deploying to Render" — but won't touch one
that already has data.)

## Using this for the Claude training exercises

Three integration points, each independent of the others:

1. **Excel export → HTML dashboard.** Signed in as staff, click "Export to
   Excel" (or hit `/export/ridgeline.xlsx`) for a live `Ridgeline_Orders.xlsx`
   — Orders, Order Items, Accounts, Products, Green Coffee Lots, Roast
   Batches, Subscriptions, all linked with real formulas (`SUMIFS`,
   `COUNTIFS`, `IF`), not pasted-in values. Good starting point for Claude
   for Excel to explore, then for turning into an HTML dashboard.
2. **Claude in Chrome automation.** Best suited to workflows that need
   real navigation or judgment, not a single lookup — e.g. triaging pending
   wholesale orders against each account's order history, or logging a
   batch of scanned paper roast sheets into the roast log form. Point it at
   the deployed Render URL (see below) rather than localhost so it's not
   fighting a local-only server.
3. **MCP for direct Q&A.** `mcp_server/server.py` is a stdio MCP server
   with tools for pending orders, low stock, account lookups, roast
   batches, and subscriptions (see `mcp_server/README.md`). It calls the
   app's `/api/*` JSON endpoints — not the database directly — the same
   pattern a real internal connector would use, and it works against
   either localhost or the Render deployment by changing one env var.

## Deploying to Render

Push this repo to GitHub, then either use the included `render.yaml`
("New +" → "Blueprint" in the Render dashboard) or create a Web Service
manually with:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2`

Render provides `SECRET_KEY` and `RIDGELINE_API_KEY` automatically via
`render.yaml` (`generateValue: true`). The free plan has no persistent
disk, so the SQLite file resets on every redeploy or spin-down from idle —
`app/bootstrap.py` re-seeds automatically whenever it finds an empty
database, so the app always comes back with working demo data. That's
convenient for a training exercise (always a clean slate) but means
anything logged mid-session (a roast batch, an order status change) won't
survive a spin-down. If you need state to persist across a full training
day, add a paid persistent disk or point `DATABASE_URL` at a Render
Postgres instance instead.

## Demo accounts

All seeded users share the password `ridgeline123`.

| Email | Role | Notes |
|---|---|---|
| `admin@ridgelinecoffee.com` | admin | Full access, incl. user management |
| `maria@ridgelinecoffee.com` | staff | Roastery ops |
| `devon@ridgelinecoffee.com` | staff | Roastery ops |
| `orders@northsidecafe.com` | customer | Wholesale — Northside Cafe (Pittsburgh) |
| `orders@mapleandco.ca` | customer | Wholesale — Maple & Co (Toronto, CAD) |
| `jsmith@example.com` | customer | Retail — has an active subscription |
| `ana.ruiz@example.com` | customer | Retail — has an active subscription |

## Data model at a glance

`User` → optionally linked to a `Customer` (wholesale account or retail
subscriber) → `Order`s, `Shipment`s, and `Subscription`s. Truck shipments
connect customer `Warehouse`s to a capacity-limited `TruckingService`.
`Product` (roasted SKU) is produced from a `GreenCoffeeLot` via a `RoastBatch`. See `app/models.py`
for the full schema — it's plain SQLAlchemy models, so it maps cleanly onto
a SQL Server table set if you want to mirror it there for the SQL Server
demo, or export `Ridgeline_Orders`-style views for the Excel demo.

## Project layout

```
run.py                 entrypoint
config.py               config (reads DATABASE_URL / SECRET_KEY from env if set)
seed.py                 CLI demo data loader (destructive reset)
Procfile, render.yaml   Render deployment config
app/
  __init__.py            app factory, blueprint registration, calls bootstrap
  bootstrap.py            non-destructive first-boot seeding
  demo_data.py             shared seed data (used by seed.py and bootstrap.py)
  models.py                SQLAlchemy models, including shipping and warehouses
  api.py                   internal JSON API (X-API-Key auth), used by MCP server
  export.py, export_routes.py   Excel workbook builder + route
  auth.py, dashboard.py, customers.py, catalog.py,
  roasting.py, orders.py, shipping.py, subscriptions.py, admin.py   blueprints
  templates/               Jinja2 templates, one folder per blueprint
  static/css/style.css      design system (single stylesheet)
mcp_server/
  server.py               stdio MCP server (calls app/api.py over HTTP)
  README.md                Claude Desktop config + tool reference
```

## Notes for extending it

- Default DB is SQLite (`ridgeline.db`) for zero-setup local running. Set
  `DATABASE_URL` (e.g. a SQL Server connection string via `pyodbc`/`mssql+pyodbc://`)
  to point it elsewhere — the models don't use anything SQLite-specific.
- No email sending, payment processing, or real auth hardening (password
  reset, rate limiting, etc.) — this is a demo backend, not a production
  storefront.
- `SECRET_KEY` defaults to a dev value; set a real one via env var before
  putting this anywhere but localhost.
- `RIDGELINE_API_KEY` (default `dev-api-key-change-me`) guards the `/api/*`
  routes the MCP server calls — set it to the same value on both sides.
