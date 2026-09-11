from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import RoastBatch, GreenCoffeeLot, Product

bp = Blueprint("roasting", __name__, url_prefix="/roasting")


def staff_only():
    if not current_user.is_staff:
        abort(403)


@bp.route("/")
@login_required
def index():
    staff_only()
    batches = RoastBatch.query.order_by(RoastBatch.roast_date.desc()).all()
    lots = GreenCoffeeLot.query.filter(GreenCoffeeLot.weight_kg_remaining > 0).order_by(
        GreenCoffeeLot.origin
    ).all()
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template("roasting/index.html", batches=batches, lots=lots, products=products)


@bp.route("/log", methods=["POST"])
@login_required
def log_batch():
    staff_only()

    lot = GreenCoffeeLot.query.get_or_404(request.form.get("lot_id", type=int))
    product = Product.query.get_or_404(request.form.get("product_id", type=int))
    green_weight = request.form.get("green_weight_kg", type=float)
    roasted_weight = request.form.get("roasted_weight_kg", type=float)
    roast_level = request.form.get("roast_level", "medium")
    notes = request.form.get("notes", "")

    if not green_weight or green_weight <= 0:
        flash("Enter a green weight greater than zero.", "error")
        return redirect(url_for("roasting.index"))

    if green_weight > float(lot.weight_kg_remaining):
        flash(
            f"Lot {lot.lot_code} only has {lot.weight_kg_remaining} kg remaining.", "error"
        )
        return redirect(url_for("roasting.index"))

    count_today = RoastBatch.query.filter(
        RoastBatch.roast_date == date.today()
    ).count()
    batch_number = f"RB-{date.today().strftime('%Y%m%d')}-{count_today + 1:02d}"

    batch = RoastBatch(
        batch_number=batch_number,
        lot=lot,
        product=product,
        roast_date=date.today(),
        green_weight_kg=green_weight,
        roasted_weight_kg=roasted_weight,
        roast_level=roast_level,
        notes=notes,
        roasted_by=current_user.name,
    )
    lot.weight_kg_remaining = float(lot.weight_kg_remaining) - green_weight

    if roasted_weight:
        # 340g retail bags produced from this batch, rest held as case stock equivalent
        bags_produced = int((roasted_weight * 1000) // product.bag_weight_g)
        product.bags_in_stock = (product.bags_in_stock or 0) + bags_produced

    db.session.add(batch)
    db.session.commit()

    flash(f"Logged roast batch {batch_number}.", "success")
    return redirect(url_for("roasting.index"))
