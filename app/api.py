"""A small internal JSON API, separate from the browser session/cookie auth.

This is what the MCP server talks to (see mcp_server/server.py) — it's the
"realistic" pattern for a connector: the assistant calls a documented API,
not the database file directly, so this keeps working if the app later
moves off SQLite.

Auth: a single shared API key via the `X-API-Key` header, checked against
RIDGELINE_API_KEY (falls back to a dev default). This is intentionally
simple for a training demo, not a production auth scheme.
"""
import os

from flask import Blueprint, jsonify, request, abort

from app import db
from app.models import (
    Order, Customer, Product, GreenCoffeeLot, RoastBatch, Subscription,
    ORDER_STATUSES,
)

bp = Blueprint("api", __name__, url_prefix="/api")

API_KEY = os.environ.get("RIDGELINE_API_KEY", "dev-api-key-change-me")


@bp.before_request
def check_api_key():
    if request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="Missing or invalid X-API-Key header.")


def order_to_dict(o, include_items=False):
    data = {
        "id": o.id,
        "order_number": o.order_number,
        "customer": o.customer.name,
        "customer_id": o.customer_id,
        "order_type": o.order_type,
        "status": o.status,
        "order_date": o.order_date.isoformat(),
        "requested_ship_date": o.requested_ship_date.isoformat() if o.requested_ship_date else None,
        "total": round(o.total_amount, 2),
        "notes": o.notes or "",
    }
    if include_items:
        data["items"] = [
            {"product": i.product.name, "sku": i.product.sku, "quantity": i.quantity,
             "unit_price": float(i.unit_price), "line_total": round(i.line_total, 2)}
            for i in o.items
        ]
    return data


def customer_to_dict(c):
    return {
        "id": c.id,
        "name": c.name,
        "type": c.type,
        "email": c.email,
        "city": c.city,
        "state": c.state,
        "country": c.country,
        "currency": c.currency,
        "open_order_count": c.open_order_count,
    }


def lot_to_dict(lot):
    return {
        "id": lot.id,
        "lot_code": lot.lot_code,
        "origin": lot.origin,
        "farm_or_coop": lot.farm_or_coop,
        "arrival_date": lot.arrival_date.isoformat(),
        "weight_kg_received": float(lot.weight_kg_received),
        "weight_kg_remaining": float(lot.weight_kg_remaining),
        "cost_per_kg_usd": float(lot.cost_per_kg_usd),
        "is_low": lot.is_low,
    }


def product_to_dict(p):
    return {
        "id": p.id,
        "sku": p.sku,
        "name": p.name,
        "origin": p.origin,
        "roast_level": p.roast_level,
        "wholesale_price_per_case": float(p.wholesale_price_per_case),
        "retail_price_per_bag": float(p.retail_price_per_bag),
        "cases_in_stock": p.cases_in_stock,
        "bags_in_stock": p.bags_in_stock,
    }


def batch_to_dict(b):
    return {
        "id": b.id,
        "batch_number": b.batch_number,
        "product": b.product.name,
        "lot_code": b.lot.lot_code,
        "roast_date": b.roast_date.isoformat(),
        "green_weight_kg": float(b.green_weight_kg),
        "roasted_weight_kg": float(b.roasted_weight_kg) if b.roasted_weight_kg else None,
        "yield_pct": b.yield_pct,
        "roasted_by": b.roasted_by,
    }


def subscription_to_dict(s):
    return {
        "id": s.id,
        "customer": s.customer.name,
        "customer_id": s.customer_id,
        "product": s.product.name,
        "frequency": s.frequency,
        "quantity": s.quantity,
        "status": s.status,
        "next_ship_date": s.next_ship_date.isoformat() if s.next_ship_date else None,
    }


# ---------------- Orders ----------------

@bp.route("/orders")
def list_orders():
    query = Order.query
    status = request.args.get("status")
    order_type = request.args.get("type")
    if status:
        query = query.filter_by(status=status)
    if order_type:
        query = query.filter_by(order_type=order_type)
    orders = query.order_by(Order.order_date.desc()).limit(int(request.args.get("limit", 100))).all()
    return jsonify([order_to_dict(o) for o in orders])


@bp.route("/orders/<int:order_id>")
def get_order(order_id):
    o = db.session.get(Order, order_id) or abort(404)
    return jsonify(order_to_dict(o, include_items=True))


@bp.route("/orders/<int:order_id>/status", methods=["POST"])
def set_order_status(order_id):
    o = db.session.get(Order, order_id) or abort(404)
    new_status = (request.get_json(silent=True) or {}).get("status")
    if new_status not in ORDER_STATUSES:
        abort(400, description=f"status must be one of {ORDER_STATUSES}")
    o.status = new_status
    db.session.commit()
    return jsonify(order_to_dict(o))


# ---------------- Accounts ----------------

@bp.route("/accounts")
def list_accounts():
    query = Customer.query
    ctype = request.args.get("type")
    if ctype:
        query = query.filter_by(type=ctype)
    return jsonify([customer_to_dict(c) for c in query.order_by(Customer.name).all()])


@bp.route("/accounts/<int:customer_id>")
def get_account(customer_id):
    c = db.session.get(Customer, customer_id) or abort(404)
    data = customer_to_dict(c)
    data["orders"] = [order_to_dict(o) for o in c.orders]
    data["subscriptions"] = [subscription_to_dict(s) for s in c.subscriptions]
    return jsonify(data)


# ---------------- Products & inventory ----------------

@bp.route("/products")
def list_products():
    return jsonify([product_to_dict(p) for p in Product.query.order_by(Product.sku).all()])


@bp.route("/inventory")
def list_inventory():
    return jsonify([lot_to_dict(l) for l in GreenCoffeeLot.query.order_by(GreenCoffeeLot.lot_code).all()])


@bp.route("/inventory/low")
def list_low_inventory():
    lots = [lot_to_dict(l) for l in GreenCoffeeLot.query.all() if l.is_low]
    return jsonify(lots)


# ---------------- Roast batches ----------------

@bp.route("/roast-batches")
def list_roast_batches():
    limit = int(request.args.get("limit", 20))
    batches = RoastBatch.query.order_by(RoastBatch.roast_date.desc()).limit(limit).all()
    return jsonify([batch_to_dict(b) for b in batches])


# ---------------- Subscriptions ----------------

@bp.route("/subscriptions")
def list_subscriptions():
    query = Subscription.query
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)
    return jsonify([subscription_to_dict(s) for s in query.all()])


@bp.route("/subscriptions/<int:sub_id>/<action>", methods=["POST"])
def change_subscription(sub_id, action):
    s = db.session.get(Subscription, sub_id) or abort(404)
    if action == "pause":
        s.status = "paused"
    elif action == "resume":
        s.status = "active"
    elif action == "cancel":
        s.status = "cancelled"
    else:
        abort(404)
    db.session.commit()
    return jsonify(subscription_to_dict(s))
