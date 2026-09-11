from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import User, Customer, ROLE_ADMIN, ROLE_STAFF, ROLE_CUSTOMER

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_only():
    if not current_user.is_admin:
        abort(403)


@bp.route("/users")
@login_required
def users():
    admin_only()
    all_users = User.query.order_by(User.role, User.name).all()
    return render_template("admin/users.html", users=all_users)


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
def new_user():
    admin_only()
    customers = Customer.query.order_by(Customer.name).all()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if User.query.filter_by(email=email).first():
            flash("A user with that email already exists.", "error")
            return render_template("admin/new_user.html", customers=customers)

        role = request.form.get("role", ROLE_CUSTOMER)
        customer_id = request.form.get("customer_id", type=int) if role == ROLE_CUSTOMER else None

        user = User(
            name=request.form.get("name", "").strip(),
            email=email,
            role=role,
            customer_id=customer_id,
        )
        user.set_password(request.form.get("password") or "ridgeline123")
        db.session.add(user)
        db.session.commit()
        flash(f"Created account for {user.name}.", "success")
        return redirect(url_for("admin.users"))

    return render_template(
        "admin/new_user.html", customers=customers,
        roles=[ROLE_ADMIN, ROLE_STAFF, ROLE_CUSTOMER],
    )
