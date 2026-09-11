from datetime import date, timedelta
from decimal import Decimal

from app.models import (
    GreenCoffeeLot,
    Order,
    OrderDueDate,
    OrderItem,
    RoastBatch,
    Shipment,
)


def test_green_coffee_lot_is_low_at_fifteen_percent():
    lot = GreenCoffeeLot(
        lot_code="LOW-LOT",
        origin="Kenya",
        weight_kg_received=Decimal("100"),
        weight_kg_remaining=Decimal("15"),
        cost_per_kg_usd=Decimal("8.00"),
    )

    assert lot.is_low is True


def test_roast_batch_calculates_yield_percentage():
    batch = RoastBatch(
        batch_number="RB-TEST",
        lot_id=1,
        product_id=1,
        green_weight_kg=Decimal("25"),
        roasted_weight_kg=Decimal("21.2"),
    )

    assert batch.yield_pct == 84.8


def test_order_calculates_totals_and_truck_shipping_summary():
    order = Order(
        order_number="MODEL-TEST",
        customer_id=1,
        order_type="wholesale",
        items=[
            OrderItem(product_id=1, quantity=2, unit_price=Decimal("12.50")),
            OrderItem(product_id=1, quantity=3, unit_price=Decimal("10.00")),
        ],
        shipments=[
            Shipment(method="delivery_truck", load_number=1),
            Shipment(method="delivery_truck", load_number=2),
        ],
    )

    assert order.total_quantity == 5
    assert order.total_amount == 55.0
    assert order.shipping_summary == "Delivery Truck (2 loads)"


def test_completed_order_is_not_overdue():
    order = Order(
        order_number="DELIVERED-TEST",
        customer_id=1,
        order_type="retail",
        status="delivered",
        delivery_deadline=OrderDueDate(
            due_date=date.today() - timedelta(days=1)
        ),
    )

    assert order.is_overdue is False
