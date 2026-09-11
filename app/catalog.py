from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

from app.models import Product, GreenCoffeeLot

bp = Blueprint("catalog", __name__)


def staff_only():
    if not current_user.is_staff:
        abort(403)


@bp.route("/products")
@login_required
def products():
    items = Product.query.order_by(Product.origin).all()
    return render_template("catalog/products.html", products=items)


@bp.route("/inventory")
@login_required
def inventory():
    staff_only()
    lots = GreenCoffeeLot.query.order_by(GreenCoffeeLot.arrival_date.desc()).all()
    return render_template("catalog/inventory.html", lots=lots)
