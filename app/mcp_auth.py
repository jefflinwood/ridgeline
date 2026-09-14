"""Browser sign-in bridge for the MCP OAuth authorization flow."""
import hashlib
import secrets

from flask import Blueprint, abort, current_app, redirect, render_template, request

from mcp_server.oauth import oauth_provider


bp = Blueprint("mcp_auth", __name__)


def _password_fingerprint(password):
    return hashlib.sha256(password.encode()).hexdigest()


@bp.route("/oauth/authorize", methods=["GET", "POST"])
def authorize():
    request_id = request.args.get("request_id") or request.form.get("request_id", "")
    class_password = current_app.config.get("MCP_CLASS_PASSWORD")
    if not class_password:
        abort(503, description="MCP authentication is not configured.")

    if request.method == "GET":
        return render_template(
            "auth/mcp_authorize.html",
            request_id=request_id,
            error=None,
            force_bare_layout=True,
        )

    submitted_password = request.form.get("password", "")
    authenticated = secrets.compare_digest(
        _password_fingerprint(submitted_password),
        _password_fingerprint(class_password),
    )
    if not authenticated:
        return render_template(
            "auth/mcp_authorize.html",
            request_id=request_id,
            error="That class password is not correct.",
            force_bare_layout=True,
        ), 401

    try:
        redirect_url = oauth_provider.approve_authorization(
            request_id,
            subject="ridgeline-class",
        )
    except ValueError as exc:
        abort(400, description=str(exc))
    return redirect(redirect_url)
