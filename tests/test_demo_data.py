from app import create_app, db
from app.demo_data import DEMO_ORDER_COUNT, populate
from app.models import Order, OrderDueDate, OrderItem, Shipment


class SeedTestConfig:
    TESTING = True
    SECRET_KEY = "seed-test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_SEED = False


def test_populate_creates_complete_large_order_history():
    app = create_app(SeedTestConfig)

    with app.app_context():
        db.create_all()
        counts = populate()
        db.session.commit()

        assert counts["orders"] == DEMO_ORDER_COUNT
        assert Order.query.count() == DEMO_ORDER_COUNT
        assert OrderItem.query.count() >= DEMO_ORDER_COUNT
        assert Shipment.query.count() >= DEMO_ORDER_COUNT
        assert OrderDueDate.query.count() == DEMO_ORDER_COUNT
        assert {status for status, in db.session.query(Order.status).distinct()} == {
            "pending", "confirmed", "roasting", "shipped", "delivered", "cancelled"
        }
        assert {order_type for order_type, in db.session.query(Order.order_type).distinct()} == {
            "wholesale", "retail"
        }
