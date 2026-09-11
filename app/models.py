from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# --- Roles & enums (kept as plain strings for SQLite/SQL Server portability) ---
ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_CUSTOMER = "customer"

CUSTOMER_WHOLESALE = "wholesale"
CUSTOMER_RETAIL = "retail"

ORDER_STATUSES = ["pending", "confirmed", "roasting", "shipped", "delivered", "cancelled"]
SUBSCRIPTION_FREQUENCIES = ["weekly", "biweekly", "monthly"]
SUBSCRIPTION_STATUSES = ["active", "paused", "cancelled"]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_CUSTOMER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Only set when role == customer: links the login to their account record
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    customer = db.relationship("Customer", back_populates="users")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_staff(self):
        return self.role in (ROLE_ADMIN, ROLE_STAFF)

    @property
    def is_customer(self):
        return self.role == ROLE_CUSTOMER

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Customer(db.Model):
    """A wholesale account (cafe, hotel, office) or a retail subscriber."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    type = db.Column(db.String(20), nullable=False, default=CUSTOMER_RETAIL)  # wholesale | retail
    email = db.Column(db.String(160))
    phone = db.Column(db.String(40))
    address = db.Column(db.String(200))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    country = db.Column(db.String(80), default="USA")
    currency = db.Column(db.String(3), default="USD")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", back_populates="customer")
    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    subscriptions = db.relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )

    @property
    def is_wholesale(self):
        return self.type == CUSTOMER_WHOLESALE

    @property
    def open_order_count(self):
        return sum(1 for o in self.orders if o.status not in ("delivered", "cancelled"))

    def __repr__(self):
        return f"<Customer {self.name} ({self.type})>"


class Product(db.Model):
    """A roasted coffee SKU, sold by the case (wholesale) or by the bag (retail)."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    origin = db.Column(db.String(80), nullable=False)
    process = db.Column(db.String(40))  # washed, natural, honey...
    roast_level = db.Column(db.String(20), nullable=False)  # light, medium, dark
    wholesale_price_per_case = db.Column(db.Numeric(10, 2), nullable=False)
    retail_price_per_bag = db.Column(db.Numeric(10, 2), nullable=False)
    bag_weight_g = db.Column(db.Integer, default=340)
    cases_in_stock = db.Column(db.Integer, default=0)
    bags_in_stock = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Product {self.sku} {self.name}>"


class GreenCoffeeLot(db.Model):
    """A purchased lot of unroasted (green) coffee sitting in the warehouse."""

    __tablename__ = "green_coffee_lots"

    id = db.Column(db.Integer, primary_key=True)
    lot_code = db.Column(db.String(30), unique=True, nullable=False)
    origin = db.Column(db.String(80), nullable=False)
    farm_or_coop = db.Column(db.String(120))
    process = db.Column(db.String(40))
    arrival_date = db.Column(db.Date, default=date.today)
    weight_kg_received = db.Column(db.Numeric(10, 2), nullable=False)
    weight_kg_remaining = db.Column(db.Numeric(10, 2), nullable=False)
    cost_per_kg_usd = db.Column(db.Numeric(10, 2), nullable=False)
    supplier_currency = db.Column(db.String(3), default="USD")

    roast_batches = db.relationship("RoastBatch", back_populates="lot")

    @property
    def is_low(self):
        # Flag lots below 15% of what arrived as running low
        if not self.weight_kg_received:
            return False
        return float(self.weight_kg_remaining) <= float(self.weight_kg_received) * 0.15

    def __repr__(self):
        return f"<GreenCoffeeLot {self.lot_code} {self.origin}>"


class RoastBatch(db.Model):
    """A single roast run: green weight in, roast level, finished weight out."""

    __tablename__ = "roast_batches"

    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(30), unique=True, nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey("green_coffee_lots.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    roast_date = db.Column(db.Date, default=date.today)
    green_weight_kg = db.Column(db.Numeric(10, 2), nullable=False)
    roasted_weight_kg = db.Column(db.Numeric(10, 2))
    roast_level = db.Column(db.String(20))
    notes = db.Column(db.Text)
    roasted_by = db.Column(db.String(120))

    lot = db.relationship("GreenCoffeeLot", back_populates="roast_batches")
    product = db.relationship("Product")

    @property
    def yield_pct(self):
        if not self.roasted_weight_kg or not self.green_weight_kg:
            return None
        return round(float(self.roasted_weight_kg) / float(self.green_weight_kg) * 100, 1)

    def __repr__(self):
        return f"<RoastBatch {self.batch_number}>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # wholesale | retail
    status = db.Column(db.String(20), nullable=False, default="pending")
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    requested_ship_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    customer = db.relationship("Customer", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return sum((item.line_total for item in self.items), start=0)

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @property
    def line_total(self):
        return float(self.unit_price) * self.quantity


class Subscription(db.Model):
    """A recurring retail bag subscription (or a wholesale standing order)."""

    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    frequency = db.Column(db.String(20), nullable=False, default="monthly")
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="active")
    next_ship_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="subscriptions")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<Subscription {self.customer_id}:{self.product_id}>"
