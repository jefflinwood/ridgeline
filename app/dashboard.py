from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Order, Subscription, GreenCoffeeLot, Product, Customer

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    if current_user.is_staff:
        open_orders = Order.query.filter(Order.status.notin_(["delivered", "cancelled"])).all()
        low_lots = [lot for lot in GreenCoffeeLot.query.all() if lot.is_low]
        active_subs = Subscription.query.filter_by(status="active").count()
        wholesale_count = Customer.query.filter_by(type="wholesale").count()
        retail_count = Customer.query.filter_by(type="retail").count()
        low_stock_products = Product.query.filter(Product.cases_in_stock < 5).all()
        return render_template(
            "dashboard/staff.html",
            open_orders=open_orders,
            low_lots=low_lots,
            active_subs=active_subs,
            wholesale_count=wholesale_count,
            retail_count=retail_count,
            low_stock_products=low_stock_products,
        )

    # customer view
    customer = current_user.customer
    orders = customer.orders if customer else []
    subscriptions = customer.subscriptions if customer else []
    return render_template(
        "dashboard/customer.html", customer=customer, orders=orders, subscriptions=subscriptions
    )
