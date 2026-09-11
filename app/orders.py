from datetime import date, datetime
from math import ceil

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import (
    Order, OrderItem, OrderDueDate, Customer, Product, Shipment, TruckingService, Warehouse,
    ORDER_STATUSES, SHIPPING_METHODS, SHIPPING_METHOD_LABELS, SERVICE_AREAS,
)

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
        shipment_status = {
            "confirmed": "ready", "roasting": "ready", "shipped": "in_transit",
            "delivered": "delivered", "cancelled": "exception",
        }.get(new_status)
        if shipment_status:
            for shipment in order.shipments:
                shipment.status = shipment_status
        db.session.commit()
        flash(f"Order {order.order_number} marked {new_status}.", "success")
    return redirect(url_for("orders.detail", order_id=order.id))


@bp.route("/<int:order_id>/due-date", methods=["POST"])
@login_required
def update_due_date(order_id):
    if not current_user.is_staff:
        abort(403)
    order = Order.query.get_or_404(order_id)
    try:
        due_date = date.fromisoformat(request.form.get("due_date", ""))
    except ValueError:
        flash("Enter a valid delivery due date.", "error")
        return redirect(url_for("orders.detail", order_id=order.id))
    if order.requested_ship_date and due_date < order.requested_ship_date:
        flash("The delivery due date cannot be before the requested ship date.", "error")
        return redirect(url_for("orders.detail", order_id=order.id))
    if order.delivery_deadline:
        order.delivery_deadline.due_date = due_date
    else:
        order.delivery_deadline = OrderDueDate(due_date=due_date)
    db.session.commit()
    flash(f"Order {order.order_number} is due {due_date.strftime('%b %-d, %Y')}.", "success")
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
    customer_ids = [customer.id for customer in customers]
    warehouses = (
        Warehouse.query.filter(Warehouse.customer_id.in_(customer_ids))
        .order_by(Warehouse.customer_id, Warehouse.name).all()
    )
    trucking_services = (
        TruckingService.query.filter_by(active=True)
        .order_by(TruckingService.capacity_cases).all()
    )

    def render_new_order():
        return render_template(
            "orders/new.html", customers=customers, products=products,
            warehouses=warehouses, trucking_services=trucking_services,
            shipping_methods=SHIPPING_METHOD_LABELS,
        )

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
            return render_new_order()

        shipping_method = request.form.get("shipping_method", "")
        if shipping_method not in SHIPPING_METHODS:
            flash("Choose a valid shipping method.", "error")
            return render_new_order()

        requested_ship_date = None
        if request.form.get("requested_ship_date"):
            try:
                requested_ship_date = date.fromisoformat(request.form["requested_ship_date"])
            except ValueError:
                flash("Enter a valid requested ship date.", "error")
                return render_new_order()

        try:
            due_date = date.fromisoformat(request.form.get("due_date", ""))
        except ValueError:
            flash("Enter a valid delivery due date.", "error")
            return render_new_order()
        if requested_ship_date and due_date < requested_ship_date:
            flash("The delivery due date cannot be before the requested ship date.", "error")
            return render_new_order()

        trucking_service = None
        destination = None
        if shipping_method == "delivery_truck":
            trucking_service = db.session.get(
                TruckingService, request.form.get("trucking_service_id", type=int)
            )
            destination = db.session.get(
                Warehouse, request.form.get("warehouse_id", type=int)
            )
            if customer.type != "wholesale" or not trucking_service or not destination:
                flash("Truck delivery requires a trucking service and warehouse.", "error")
                return render_new_order()
            if not trucking_service.active or destination.customer_id != customer.id:
                abort(400)
            if SERVICE_AREAS.index(trucking_service.service_area) < SERVICE_AREAS.index(destination.service_area):
                flash(
                    f"{trucking_service.name} does not cover {destination.service_area.replace('_', '-')} deliveries.",
                    "error",
                )
                return render_new_order()

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
            requested_ship_date=requested_ship_date,
            delivery_deadline=OrderDueDate(due_date=due_date),
            items=items,
            notes=request.form.get("notes", ""),
        )
        db.session.add(order)
        if shipping_method == "delivery_truck":
            cases_remaining = sum(item.quantity for item in items)
            load_count = ceil(cases_remaining / trucking_service.capacity_cases)
            for load_number in range(1, load_count + 1):
                cases = min(cases_remaining, trucking_service.capacity_cases)
                order.shipments.append(Shipment(
                    method=shipping_method, status="planned",
                    scheduled_ship_date=requested_ship_date,
                    trucking_service=trucking_service, warehouse=destination,
                    load_number=load_number, cases=cases,
                ))
                cases_remaining -= cases
        else:
            order.shipments.append(Shipment(
                method=shipping_method, status="planned",
                scheduled_ship_date=requested_ship_date,
            ))
        db.session.commit()
        flash(
            f"Order {order_number} created with {order.shipping_summary.lower()}.",
            "success",
        )
        return redirect(url_for("orders.detail", order_id=order.id))

    return render_new_order()
