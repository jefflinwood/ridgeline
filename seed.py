"""Populate a fresh database with demo data for Ridgeline Coffee Roasters.

Run with:  python seed.py
Destructive: drops and recreates all tables first, so it always resets to
a clean demo state. For non-destructive first-boot seeding (e.g. Render),
see app/bootstrap.py, which uses the same app/demo_data.py::populate().
"""
from app import create_app, db
from app.demo_data import populate, DEFAULT_PASSWORD

app = create_app()


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()
        counts = populate()
        db.session.commit()
        print("Seeded Ridgeline Coffee demo data.")
        print(f"  Products: {counts['products']}  Lots: {counts['lots']}  Batches: {counts['batches']}")
        print(f"  Customers: {counts['customers']}  Orders: {counts['orders']}  Subscriptions: {counts['subscriptions']}")
        print(f"  Users: {counts['users']} (all passwords: {DEFAULT_PASSWORD})")


if __name__ == "__main__":
    run()
