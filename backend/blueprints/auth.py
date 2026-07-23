#  User Registration and Login
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_acc
from extensions import db, bcrypt
from models import User

# create blueprint object
auth_bp =Blueprint("auth",__name__, url_prefix="/api/auth");

# is it an email?
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# route decorator
@auth_bp.post("/register")
def register():
	# reads the JSON data
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()  
    password = data.get("password") or ""

	# check if it is valid 
    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are all required."}), 400 # 400 Bad Request
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Please enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409 # 409 Request conflicts with existing data

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(name=name, email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created. You can now log in."}), 201  # 201 Created

# route decorator
@auth_bp.post("/login")
def login():
	# read JSON Body
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # find the user in the database
    user = User.query.filter_by(email=email).first()

    # verify the password
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password."}), 401

    # create a JSON Web Token with acccess token and user 
    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 200    

@auth_bp.get("/me")
@jwt_required()
def me():
    # reads the id put into the token at login time.
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user.to_dict()), 200
