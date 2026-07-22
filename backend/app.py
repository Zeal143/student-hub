from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, jwt, bcrypt


def create_app(config_class=Config):
    """
    Application factory: builds and configures a Flask app instance.

    Using a factory (instead of one global `app = Flask(__name__)`) means
    the same codebase can produce a normal app for `python app.py` and a
    separately-configured app for the test suite (see tests/conftest.py,
    which passes `config_class=TestConfig` to point at SQLite instead of
    the real MySQL database).
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Each extension is a single shared instance (see extensions.py) that
    # gets bound to *this* app here, rather than being created per-app.
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app)  # tighten origins before deploying to production

    # Blueprints are imported here (not at module load time) so that each
    # blueprint's `from models import ...` runs after db.init_app has a
    # chance to be configured for the right app/config.
    from blueprints.auth import auth_bp
    from blueprints.expenses import expenses_bp
    from blueprints.budgets import budgets_bp
    from blueprints.savings import savings_bp
    from blueprints.bins import bins_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.categories import categories_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(bins_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categories_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Auto-create any missing tables against the real MySQL database on
    # startup. Fine for a student project; a production app would use proper
    # migrations (e.g. Flask-Migrate/Alembic) instead of db.create_all().
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
