#import libraries
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, jwt, bcrypt


def create_app(config_class=Config):
#create web application with flask
    app = Flask(__name__)
    #load the configuration class
    app.config.from_object(config_class)

   #initialize Extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app)  # enable CORS

    # Blueprints are imported 
    from blueprints.auth import auth_bp
    from blueprints.expenses import expenses_bp
    from blueprints.budgets import budgets_bp
    from blueprints.savings import savings_bp
    from blueprints.bins import bins_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.categories import categories_bp

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(bins_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categories_bp)

    #check for deployment and monitoring
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

#create applicaiton
app = create_app()
# run the application
if __name__ == "__main__":
    # create tables
    with app.app_context():
        db.create_all()
    #start server
    app.run(debug=True, port=5000)
