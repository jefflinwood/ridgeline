from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "info"


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth import bp as auth_bp
    from app.dashboard import bp as dashboard_bp
    from app.customers import bp as customers_bp
    from app.catalog import bp as catalog_bp
    from app.roasting import bp as roasting_bp
    from app.orders import bp as orders_bp
    from app.subscriptions import bp as subscriptions_bp
    from app.admin import bp as admin_bp
    from app.export_routes import bp as export_bp
    from app.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(roasting_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year}

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    with app.app_context():
        from app.bootstrap import ensure_seeded
        ensure_seeded()

    return app
