from datetime import date

from flask import Blueprint, send_file, abort
from flask_login import login_required, current_user

from app.export import build_workbook

bp = Blueprint("export", __name__, url_prefix="/export")


@bp.route("/ridgeline.xlsx")
@login_required
def ridgeline_xlsx():
    if not current_user.is_staff:
        abort(403)
    buf = build_workbook()
    filename = f"Ridgeline_Orders_{date.today().isoformat()}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
