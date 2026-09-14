from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app import create_app, db
from app.models import (
    Customer,
    Order,
    OrderDueDate,
    OrderItem,
    Product,
    Shipment,
    User,
)


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_SEED = False
    MCP_CLASS_PASSWORD = "test-class-password"


@pytest.fixture
def app():
    test_app = create_app(TestConfig)

    with test_app.app_context():
        db.create_all()

        northside = Customer(
            name="Northside Cafe",
            type="wholesale",
            email="orders@northside.test",
            address="1 North Ave",
            city="Pittsburgh",
            state="PA",
        )
        competitor = Customer(
            name="Southside Cafe",
            type="wholesale",
            email="orders@southside.test",
            address="2 South Ave",
            city="Pittsburgh",
            state="PA",
        )
        product = Product(
            sku="TEST-MD",
            name="Test Blend",
            origin="Colombia",
            roast_level="medium",
            wholesale_price_per_case=Decimal("100.00"),
            retail_price_per_bag=Decimal("15.00"),
            cases_in_stock=10,
            bags_in_stock=20,
        )
        db.session.add_all([northside, competitor, product])
        db.session.flush()

        users = [
            User(name="Staff User", email="staff@example.test", role="staff"),
            User(
                name="Northside User",
                email="customer@example.test",
                role="customer",
                customer=northside,
            ),
        ]
        for user in users:
            user.set_password("test-password")
        db.session.add_all(users)

        own_order = Order(
            order_number="WS-TEST-001",
            customer=northside,
            order_type="wholesale",
            status="pending",
            order_date=datetime(2026, 9, 1, 9, 0),
            requested_ship_date=date.today() + timedelta(days=2),
            items=[OrderItem(product=product, quantity=2, unit_price=Decimal("100.00"))],
            shipments=[Shipment(method="ups", status="planned", load_number=1)],
        )
        other_order = Order(
            order_number="WS-TEST-002",
            customer=competitor,
            order_type="wholesale",
            status="confirmed",
            order_date=datetime(2026, 9, 2, 9, 0),
            requested_ship_date=date.today() - timedelta(days=3),
            delivery_deadline=OrderDueDate(due_date=date.today() - timedelta(days=1)),
            items=[OrderItem(product=product, quantity=3, unit_price=Decimal("90.00"))],
            shipments=[Shipment(method="fedex", status="ready", load_number=1)],
        )
        db.session.add_all([own_order, other_order])
        db.session.commit()

        test_app.config["TEST_IDS"] = {
            "own_order": own_order.id,
            "other_order": other_order.id,
            "product": product.id,
        }

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def log_in(email, password="test-password"):
        return client.post(
            "/login",
            data={"email": email, "password": password},
        )

    return log_in


@pytest.fixture
def api_headers(monkeypatch):
    monkeypatch.setattr("app.api.API_KEY", "test-api-key")
    return {"X-API-Key": "test-api-key"}
