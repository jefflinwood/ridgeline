from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Subscription, Customer, Product, SUBSCRIPTION_FREQUENCIES

bp = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")

FREQUENCY_DAYS = {"weekly": 7, "biweekly": 14, "monthly": 30}


@bp.route("/")
@login_required
def index():
    if current_user.is_staff:
        subs = Subscription.query.order_by(Subscription.status, Subscription.next_ship_date).all()
    else:
        if not current_user.customer:
            abort(403)
        subs = current_user.customer.subscriptions
    return render_template("subscriptions/index.html", subscriptions=subs)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if current_user.is_staff:
        customers = Customer.query.filter_by(type="retail").order_by(Customer.name).all()
    else:
        customers = [current_user.customer] if current_user.customer else []

    products = Product.query.filter_by(active=True).order_by(Product.name).all()

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        customer = Customer.query.get_or_404(customer_id)
        if not current_user.is_staff and customer.id != current_user.customer_id:
            abort(403)

        product = Product.query.get_or_404(request.form.get("product_id", type=int))
        frequency = request.form.get("frequency", "monthly")
        quantity = request.form.get("quantity", type=int) or 1

        sub = Subscription(
            customer=customer,
            product=product,
            frequency=frequency,
            quantity=quantity,
            status="active",
            next_ship_date=date.today() + timedelta(days=FREQUENCY_DAYS.get(frequency, 30)),
        )
        db.session.add(sub)
        db.session.commit()
        flash("Subscription created.", "success")
        return redirect(url_for("subscriptions.index"))

    return render_template(
        "subscriptions/new.html", customers=customers, products=products,
        frequencies=SUBSCRIPTION_FREQUENCIES,
    )


@bp.route("/<int:sub_id>/<action>", methods=["POST"])
@login_required
def change_status(sub_id, action):
    sub = Subscription.query.get_or_404(sub_id)
    if not current_user.is_staff and sub.customer_id != current_user.customer_id:
        abort(403)

    if action == "pause":
        sub.status = "paused"
        flash("Subscription paused.", "info")
    elif action == "resume":
        sub.status = "active"
        sub.next_ship_date = date.today() + timedelta(days=FREQUENCY_DAYS.get(sub.frequency, 30))
        flash("Subscription resumed.", "success")
    elif action == "cancel":
        sub.status = "cancelled"
        flash("Subscription cancelled.", "info")
    else:
        abort(404)

    db.session.commit()
    return redirect(url_for("subscriptions.index"))
