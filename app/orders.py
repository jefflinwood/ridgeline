from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import Order, OrderItem, Customer, Product, ORDER_STATUSES

bp = Blueprint("orders", __name__, url_prefix="/orders")


def _visible_orders_query():
    query = Order.query
    if current_user.is_staff:
        status = request.args.get("status")
        order_type = request.args.get("type")
        if status:
            query = query.filter_by(status=status)
        if order_type:
            query = query.filter_by(order_type=order_type)
    else:
        if not current_user.customer:
            abort(403)
        query = query.filter_by(customer_id=current_user.customer_id)
    return query.order_by(Order.order_date.desc())


@bp.route("/")
@login_required
def index():
    orders = _visible_orders_query().all()
    return render_template(
        "orders/index.html", orders=orders, statuses=ORDER_STATUSES,
        active_status=request.args.get("status"), active_type=request.args.get("type"),
    )


@bp.route("/<int:order_id>")
@login_required
def detail(order_id):
    order = Order.query.get_or_404(order_id)
    if not current_user.is_staff and order.customer_id != current_user.customer_id:
        abort(403)
    return render_template("orders/detail.html", order=order, statuses=ORDER_STATUSES)


@bp.route("/<int:order_id>/status", methods=["POST"])
@login_required
def update_status(order_id):
    if not current_user.is_staff:
        abort(403)
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status in ORDER_STATUSES:
        order.status = new_status
        db.session.commit()
        flash(f"Order {order.order_number} marked {new_status}.", "success")
    return redirect(url_for("orders.detail", order_id=order.id))


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if current_user.is_staff:
        customers = Customer.query.order_by(Customer.name).all()
    else:
        if not current_user.customer:
            abort(403)
        customers = [current_user.customer]

    products = Product.query.filter_by(active=True).order_by(Product.name).all()

    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        customer = Customer.query.get_or_404(customer_id)

        if not current_user.is_staff and customer.id != current_user.customer_id:
            abort(403)

        product_ids = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")

        items = []
        for pid, qty in zip(product_ids, quantities):
            qty = int(qty or 0)
            if qty <= 0:
                continue
            product = Product.query.get_or_404(int(pid))
            unit_price = (
                product.wholesale_price_per_case
                if customer.type == "wholesale"
                else product.retail_price_per_bag
            )
            items.append(OrderItem(product=product, quantity=qty, unit_price=unit_price))

        if not items:
            flash("Add at least one product with a quantity.", "error")
            return render_template("orders/new.html", customers=customers, products=products)

        count_today = Order.query.filter(
            db.func.date(Order.order_date) == date.today()
        ).count()
        order_number = f"{'WS' if customer.type == 'wholesale' else 'RT'}-{date.today().strftime('%Y%m%d')}-{count_today + 1:03d}"

        order = Order(
            order_number=order_number,
            customer=customer,
            order_type=customer.type,
            status="pending",
            order_date=datetime.utcnow(),
            items=items,
            notes=request.form.get("notes", ""),
        )
        db.session.add(order)
        db.session.commit()
        flash(f"Order {order_number} created.", "success")
        return redirect(url_for("orders.detail", order_id=order.id))

    return render_template("orders/new.html", customers=customers, products=products)
