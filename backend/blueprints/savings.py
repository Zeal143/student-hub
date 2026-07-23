from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import SavingsGoal

#create a blue print
savings_bp = Blueprint("savings", __name__, url_prefix="/api/savings")

#Get the savings 
@savings_bp.get("")
@jwt_required()
def list_goals():
    user_id = int(get_jwt_identity())
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()
    return jsonify([g.to_dict() for g in goals]), 200


#Create the new savings 
@savings_bp.post("")
@jwt_required()
def create_goal():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Goal name is required."}), 400

    try:
        target_amount = float(data.get("target_amount"))
        if target_amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Target amount must be a positive number."}), 400

    # The target date is optional
    target_date = None
    if data.get("target_date"):
        try:
            target_date = datetime.strptime(data["target_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Target date must be in YYYY-MM-DD format."}), 400

    goal = SavingsGoal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        current_amount=0,  # every new goal starts at zero saved
        target_date=target_date,
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify(goal.to_dict()), 201


#Update the savings goal 
@savings_bp.put("/<int:goal_id>")
@jwt_required()
def update_goal(goal_id):

    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}

    if "current_amount" in data:
        try:
            goal.current_amount = float(data["current_amount"])
        except (TypeError, ValueError):
            return jsonify({"error": "current_amount must be a number."}), 400

    if "target_amount" in data:
        try:
            goal.target_amount = float(data["target_amount"])
        except (TypeError, ValueError):
            return jsonify({"error": "target_amount must be a number."}), 400

    db.session.commit()
    return jsonify(goal.to_dict()), 200

#Delete the savings goal 
@savings_bp.delete("/<int:goal_id>")
@jwt_required()
def delete_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    return jsonify({"message": "Savings goal deleted."}), 200
