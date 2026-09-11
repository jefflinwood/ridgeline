"""Shared demo-data population logic for Ridgeline Coffee Roasters.

Used by both seed.py (CLI, destructive reset) and app/bootstrap.py
(non-destructive, runs once on first boot e.g. on Render).
"""
from datetime import date, datetime, timedelta

from app import db
from app.models import (
    User, Customer, Product, GreenCoffeeLot, RoastBatch, Order, OrderItem, Subscription,
    ROLE_ADMIN, ROLE_STAFF, ROLE_CUSTOMER,
)

DEFAULT_PASSWORD = "ridgeline123"


def populate():
    """Add demo Products/Lots/Batches/Customers/Orders/Subscriptions/Users
    to the current db.session. Does not commit — caller commits."""
    # ---------------- Products ----------------
    products = [
        Product(sku="ETH-YIR-LT", name="Ethiopia Yirgacheffe", origin="Ethiopia",
                process="Natural", roast_level="light",
                wholesale_price_per_case=185.00, retail_price_per_bag=19.00,
                cases_in_stock=22, bags_in_stock=140),
        Product(sku="COL-HUI-MD", name="Colombia Huila", origin="Colombia",
                process="Washed", roast_level="medium",
                wholesale_price_per_case=165.00, retail_price_per_bag=17.00,
                cases_in_stock=30, bags_in_stock=210),
        Product(sku="SUM-MAN-DK", name="Sumatra Mandheling", origin="Indonesia",
                process="Wet-hulled", roast_level="dark",
                wholesale_price_per_case=170.00, retail_price_per_bag=17.50,
                cases_in_stock=4, bags_in_stock=38),
        Product(sku="GUA-ANT-MD", name="Guatemala Antigua", origin="Guatemala",
                process="Washed", roast_level="medium",
                wholesale_price_per_case=175.00, retail_price_per_bag=18.00,
                cases_in_stock=18, bags_in_stock=95),
        Product(sku="KEN-AA-LT", name="Kenya AA", origin="Kenya",
                process="Washed", roast_level="light",
                wholesale_price_per_case=195.00, retail_price_per_bag=20.00,
                cases_in_stock=12, bags_in_stock=60),
        Product(sku="BRA-CER-MD", name="Brazil Cerrado", origin="Brazil",
                process="Natural", roast_level="medium",
                wholesale_price_per_case=150.00, retail_price_per_bag=15.50,
                cases_in_stock=26, bags_in_stock=180),
    ]
    db.session.add_all(products)
    db.session.flush()
    by_sku = {p.sku: p for p in products}

    # ---------------- Green coffee lots ----------------
    lots = [
        GreenCoffeeLot(lot_code="GC-24-101", origin="Ethiopia", farm_or_coop="Yirgacheffe Coop Union",
                        process="Natural", arrival_date=date(2026, 6, 12),
                        weight_kg_received=300, weight_kg_remaining=210, cost_per_kg_usd=8.40),
        GreenCoffeeLot(lot_code="GC-24-102", origin="Colombia", farm_or_coop="Finca El Mirador",
                        process="Washed", arrival_date=date(2026, 6, 20),
                        weight_kg_received=400, weight_kg_remaining=260, cost_per_kg_usd=6.90),
        GreenCoffeeLot(lot_code="GC-24-103", origin="Indonesia", farm_or_coop="Lintong Growers Group",
                        process="Wet-hulled", arrival_date=date(2026, 5, 2),
                        weight_kg_received=250, weight_kg_remaining=28, cost_per_kg_usd=7.20),
        GreenCoffeeLot(lot_code="GC-24-104", origin="Guatemala", farm_or_coop="Finca Los Volcanes",
                        process="Washed", arrival_date=date(2026, 7, 1),
                        weight_kg_received=300, weight_kg_remaining=190, cost_per_kg_usd=7.60),
        GreenCoffeeLot(lot_code="GC-24-105", origin="Kenya", farm_or_coop="Nyeri Hill Cooperative",
                        process="Washed", arrival_date=date(2026, 7, 15),
                        weight_kg_received=200, weight_kg_remaining=25, cost_per_kg_usd=9.10),
        GreenCoffeeLot(lot_code="GC-24-106", origin="Brazil", farm_or_coop="Fazenda Santa Ines",
                        process="Natural", arrival_date=date(2026, 6, 28),
                        weight_kg_received=350, weight_kg_remaining=240, cost_per_kg_usd=5.80),
    ]
    db.session.add_all(lots)
    db.session.flush()
    by_lot = {l.lot_code: l for l in lots}

    # ---------------- Roast batches ----------------
    batches = [
        RoastBatch(batch_number="RB-20260801-01", lot=by_lot["GC-24-101"], product=by_sku["ETH-YIR-LT"],
                   roast_date=date(2026, 8, 1), green_weight_kg=25, roasted_weight_kg=21.2,
                   roast_level="light", roasted_by="Maria Alvarez", notes="First crack at 9:40, dropped early for brightness."),
        RoastBatch(batch_number="RB-20260803-01", lot=by_lot["GC-24-102"], product=by_sku["COL-HUI-MD"],
                   roast_date=date(2026, 8, 3), green_weight_kg=30, roasted_weight_kg=25.8,
                   roast_level="medium", roasted_by="Maria Alvarez"),
        RoastBatch(batch_number="RB-20260805-01", lot=by_lot["GC-24-103"], product=by_sku["SUM-MAN-DK"],
                   roast_date=date(2026, 8, 5), green_weight_kg=20, roasted_weight_kg=16.4,
                   roast_level="dark", roasted_by="Devon Park", notes="Ran a touch hot — watch drop temp next batch."),
        RoastBatch(batch_number="RB-20260807-01", lot=by_lot["GC-24-105"], product=by_sku["KEN-AA-LT"],
                   roast_date=date(2026, 8, 7), green_weight_kg=18, roasted_weight_kg=15.1,
                   roast_level="light", roasted_by="Maria Alvarez"),
    ]
    db.session.add_all(batches)

    # ---------------- Customers ----------------
    wholesale = [
        Customer(name="Northside Cafe", type="wholesale", email="orders@northsidecafe.com",
                 phone="412-555-0148", address="118 E Ohio St", city="Pittsburgh", state="PA",
                 country="USA", currency="USD",
                 notes="Standing weekly order, delivers Tuesdays."),
        Customer(name="Maple & Co", type="wholesale", email="orders@mapleandco.ca",
                 phone="416-555-0199", address="44 Ossington Ave", city="Toronto", state="ON",
                 country="Canada", currency="CAD",
                 notes="Invoiced in CAD; watch FX on the margin model."),
        Customer(name="Kensington Hotel Group", type="wholesale", email="procurement@kensingtonhg.co.uk",
                 phone="+44 20 7946 0958", address="12 Belgrave Rd", city="London", state="",
                 country="UK", currency="GBP",
                 notes="Supplies in-room and lobby cafe service across 3 properties."),
        Customer(name="Daily Grind Offices", type="wholesale", email="facilities@dailygrindhq.com",
                 phone="512-555-0122", address="900 Congress Ave", city="Austin", state="TX",
                 country="USA", currency="USD"),
    ]
    retail = [
        Customer(name="John Smith", type="retail", email="jsmith@example.com",
                 phone="215-555-0110", address="22 Pine St", city="Philadelphia", state="PA", country="USA"),
        Customer(name="Ana Ruiz", type="retail", email="ana.ruiz@example.com",
                 phone="303-555-0177", address="88 Larimer St", city="Denver", state="CO", country="USA"),
        Customer(name="Priya Nair", type="retail", email="priya.nair@example.com",
                 phone="646-555-0133", address="410 Bedford Ave", city="Brooklyn", state="NY", country="USA"),
        Customer(name="Tom Reilly", type="retail", email="tom.reilly@example.com",
                 phone="617-555-0166", address="5 Beacon St", city="Boston", state="MA", country="USA"),
    ]
    db.session.add_all(wholesale + retail)
    db.session.flush()

    northside, maple, kensington, daily_grind = wholesale
    john, ana, priya, tom = retail

    # ---------------- Orders ----------------
    def case_item(product, qty):
        return OrderItem(product=product, quantity=qty, unit_price=product.wholesale_price_per_case)

    def bag_item(product, qty):
        return OrderItem(product=product, quantity=qty, unit_price=product.retail_price_per_bag)

    orders = [
        Order(order_number="WS-20260901-001", customer=northside, order_type="wholesale",
              status="pending", order_date=datetime(2026, 9, 1, 9, 15),
              requested_ship_date=date(2026, 9, 5),
              notes="Rush the Ethiopia if possible — running low before the weekend.",
              items=[case_item(by_sku["ETH-YIR-LT"], 6), case_item(by_sku["COL-HUI-MD"], 4)]),
        Order(order_number="WS-20260828-004", customer=maple, order_type="wholesale",
              status="shipped", order_date=datetime(2026, 8, 28, 11, 0),
              requested_ship_date=date(2026, 9, 2),
              items=[case_item(by_sku["GUA-ANT-MD"], 8), case_item(by_sku["BRA-CER-MD"], 5)]),
        Order(order_number="WS-20260825-002", customer=kensington, order_type="wholesale",
              status="delivered", order_date=datetime(2026, 8, 25, 14, 30),
              requested_ship_date=date(2026, 8, 29),
              items=[case_item(by_sku["KEN-AA-LT"], 10), case_item(by_sku["ETH-YIR-LT"], 10)]),
        Order(order_number="WS-20260830-003", customer=daily_grind, order_type="wholesale",
              status="confirmed", order_date=datetime(2026, 8, 30, 8, 45),
              requested_ship_date=date(2026, 9, 6),
              items=[case_item(by_sku["BRA-CER-MD"], 3), case_item(by_sku["COL-HUI-MD"], 3)]),
        Order(order_number="RT-20260902-001", customer=john, order_type="retail",
              status="pending", order_date=datetime(2026, 9, 2, 10, 5),
              items=[bag_item(by_sku["ETH-YIR-LT"], 2)]),
        Order(order_number="RT-20260828-011", customer=ana, order_type="retail",
              status="delivered", order_date=datetime(2026, 8, 28, 16, 20),
              items=[bag_item(by_sku["KEN-AA-LT"], 1), bag_item(by_sku["GUA-ANT-MD"], 1)]),
        Order(order_number="RT-20260830-013", customer=priya, order_type="retail",
              status="shipped", order_date=datetime(2026, 8, 30, 12, 0),
              items=[bag_item(by_sku["SUM-MAN-DK"], 2)]),
    ]
    db.session.add_all(orders)

    # ---------------- Subscriptions ----------------
    subs = [
        Subscription(customer=john, product=by_sku["ETH-YIR-LT"], frequency="monthly",
                     quantity=2, status="active", next_ship_date=date(2026, 9, 15)),
        Subscription(customer=ana, product=by_sku["KEN-AA-LT"], frequency="biweekly",
                     quantity=1, status="active", next_ship_date=date(2026, 9, 10)),
        Subscription(customer=priya, product=by_sku["SUM-MAN-DK"], frequency="monthly",
                     quantity=1, status="paused", next_ship_date=None),
        Subscription(customer=tom, product=by_sku["COL-HUI-MD"], frequency="weekly",
                     quantity=1, status="active", next_ship_date=date(2026, 9, 9)),
    ]
    db.session.add_all(subs)

    # ---------------- Users ----------------
    def make_user(name, email, role, password=DEFAULT_PASSWORD, customer=None):
        u = User(name=name, email=email, role=role, customer=customer)
        u.set_password(password)
        return u

    users = [
        make_user("Admin User", "admin@ridgelinecoffee.com", ROLE_ADMIN),
        make_user("Maria Alvarez", "maria@ridgelinecoffee.com", ROLE_STAFF),
        make_user("Devon Park", "devon@ridgelinecoffee.com", ROLE_STAFF),
        make_user("Northside Cafe Orders", "orders@northsidecafe.com", ROLE_CUSTOMER, customer=northside),
        make_user("Maple & Co Orders", "orders@mapleandco.ca", ROLE_CUSTOMER, customer=maple),
        make_user("John Smith", "jsmith@example.com", ROLE_CUSTOMER, customer=john),
        make_user("Ana Ruiz", "ana.ruiz@example.com", ROLE_CUSTOMER, customer=ana),
    ]
    db.session.add_all(users)

    return {
        "products": len(products), "lots": len(lots), "batches": len(batches),
        "customers": len(wholesale) + len(retail), "orders": len(orders),
        "subscriptions": len(subs), "users": len(users),
    }
