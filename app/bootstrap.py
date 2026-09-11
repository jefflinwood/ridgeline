"""Create tables and seed demo data on first boot only.

Called from create_app() so a fresh deploy (e.g. on Render, where the
filesystem/db may not exist yet) comes up with working demo data without
a manual seed step — and so that a later restart of the *same* database
never wipes anything, unlike seed.py's CLI reset.
"""
from app import db
from app.models import User
from app.demo_data import populate


def ensure_seeded():
    db.create_all()
    if User.query.count() == 0:
        populate()
        db.session.commit()
