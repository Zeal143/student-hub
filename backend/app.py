from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, jwt, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app)  # tighten origins before deploying to production

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
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
