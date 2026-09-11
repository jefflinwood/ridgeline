from app import db
from app.models import Order


def test_customer_can_view_own_order(app, client, login):
    login("customer@example.test")

    response = client.get(f"/orders/{app.config['TEST_IDS']['own_order']}")

    assert response.status_code == 200
    assert b"WS-TEST-001" in response.data


def test_customer_cannot_view_another_customers_order(app, client, login):
    login("customer@example.test")

    response = client.get(f"/orders/{app.config['TEST_IDS']['other_order']}")

    assert response.status_code == 403


def test_staff_status_update_also_updates_shipment(app, client, login):
    login("staff@example.test")
    order_id = app.config["TEST_IDS"]["own_order"]

    response = client.post(
        f"/orders/{order_id}/status",
        data={"status": "shipped"},
    )

    assert response.status_code == 302
    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == "shipped"
        assert [shipment.status for shipment in order.shipments] == ["in_transit"]


def test_customer_cannot_update_order_status(app, client, login):
    login("customer@example.test")

    response = client.post(
        f"/orders/{app.config['TEST_IDS']['own_order']}/status",
        data={"status": "delivered"},
    )

    assert response.status_code == 403
