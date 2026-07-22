"""
Flask extension instances, created once here and shared across the app.

They're deliberately created *without* an app attached (`SQLAlchemy()`, not
`SQLAlchemy(app)`) and bound to a real app later via `.init_app(app)` in
app.py's create_app(). That's what lets create_app() be called more than
once (normal run vs. the test suite in tests/) without the extensions
getting tangled up between two different app instances.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
