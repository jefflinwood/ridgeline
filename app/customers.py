from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user

from app.models import Customer

bp = Blueprint("customers", __name__, url_prefix="/customers")


def staff_only():
    if not current_user.is_staff:
        abort(403)


@bp.route("/")
@login_required
def index():
    staff_only()
    type_filter = request.args.get("type")
    query = Customer.query
    if type_filter in ("wholesale", "retail"):
        query = query.filter_by(type=type_filter)
    customers = query.order_by(Customer.name).all()
    return render_template("customers/index.html", customers=customers, type_filter=type_filter)


@bp.route("/<int:customer_id>")
@login_required
def detail(customer_id):
    staff_only()
    customer = Customer.query.get_or_404(customer_id)
    return render_template("customers/detail.html", customer=customer)
