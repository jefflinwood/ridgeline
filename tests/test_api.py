from datetime import date, timedelta

from app import db
from app.models import Order


def test_api_requires_valid_key(client):
    assert client.get("/api/orders").status_code == 401
    assert client.get(
        "/api/orders", headers={"X-API-Key": "wrong"}
    ).status_code == 401


def test_order_detail_serializes_items_and_totals(app, client, api_headers):
    order_id = app.config["TEST_IDS"]["own_order"]

    response = client.get(f"/api/orders/{order_id}", headers=api_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["order_number"] == "WS-TEST-001"
    assert payload["total"] == 200.0
    assert payload["shipping"] == "UPS"
    assert payload["items"] == [
        {
            "line_total": 200.0,
            "product": "Test Blend",
            "quantity": 2,
            "sku": "TEST-MD",
            "unit_price": 100.0,
        }
    ]


def test_order_filters_are_applied(client, api_headers):
    response = client.get("/api/orders?status=pending", headers=api_headers)

    assert response.status_code == 200
    assert [order["order_number"] for order in response.get_json()] == ["WS-TEST-001"]


def test_api_rejects_unknown_order_status(app, client, api_headers):
    order_id = app.config["TEST_IDS"]["own_order"]

    response = client.post(
        f"/api/orders/{order_id}/status",
        headers=api_headers,
        json={"status": "lost"},
    )

    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(Order, order_id).status == "pending"


def test_due_date_cannot_precede_requested_ship_date(app, client, api_headers):
    order_id = app.config["TEST_IDS"]["own_order"]
    invalid_due_date = date.today() + timedelta(days=1)

    response = client.post(
        f"/api/orders/{order_id}/due-date",
        headers=api_headers,
        json={"due_date": invalid_due_date.isoformat()},
    )

    assert response.status_code == 400
    with app.app_context():
        assert db.session.get(Order, order_id).due_date is None
