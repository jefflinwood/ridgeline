from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from app.models import SHIPPING_METHOD_LABELS, Shipment, TruckingService

bp = Blueprint("shipping", __name__, url_prefix="/shipping")


@bp.route("/")
@login_required
def index():
    if not current_user.is_staff:
        abort(403)
    services = TruckingService.query.order_by(TruckingService.capacity_cases).all()
    shipments = Shipment.query.all()
    method_counts = {
        method: sum(1 for shipment in shipments if shipment.method == method)
        for method in SHIPPING_METHOD_LABELS
    }
    truck_loads = (
        Shipment.query.filter_by(method="delivery_truck")
        .order_by(Shipment.scheduled_ship_date.desc(), Shipment.order_id, Shipment.load_number)
        .all()
    )
    return render_template(
        "shipping/index.html", services=services, truck_loads=truck_loads,
        shipping_methods=SHIPPING_METHOD_LABELS, method_counts=method_counts,
    )
