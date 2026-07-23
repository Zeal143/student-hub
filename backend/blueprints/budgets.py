from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from extensions import db
from models import Budget, Category, Expense

#create the blueprint for budget
budgets_bp = Blueprint("budgets", __name__, url_prefix="/api/budgets")


def budgets_with_spent(user_id):

    now = datetime.utcnow()
    #get budgets
    budgets = Budget.query.filter_by(user_id=user_id).all()
    result = []
    for b in budgets:
        # Sum this category's expenses for the current month only - last
        # month's spending shouldn't count against this month's budget.
        spent = (
            db.session.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.user_id == user_id,
                Expense.category_id == b.category_id,
                func.extract("year", Expense.date) == now.year,
                func.extract("month", Expense.date) == now.month,
            )
            .scalar()
        )
        data = b.to_dict()
        data["spent"] = float(spent)
        data["remaining"] = float(b.monthly_limit) - float(spent)
        data["over_budget"] = float(spent) > float(b.monthly_limit)
        result.append(data)

    return result

#get list of budgets
@budgets_bp.get("")
@jwt_required()
def list_budgets():
    user_id = int(get_jwt_identity())
    return jsonify(budgets_with_spent(user_id)), 200

#Create a budget for a categoryor update 
@budgets_bp.post("")
@jwt_required()
def set_budget():

    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    category_id = data.get("category_id")
    if not Category.query.get(category_id):
        return jsonify({"error": "Invalid category."}), 400

    try:
        monthly_limit = float(data.get("monthly_limit"))
        if monthly_limit <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Monthly limit must be a positive number."}), 400

    
    budget = Budget.query.filter_by(user_id=user_id, category_id=category_id).first()
    if budget:
        budget.monthly_limit = monthly_limit
    else:
        budget = Budget(user_id=user_id, category_id=category_id, monthly_limit=monthly_limit)
        db.session.add(budget)

    db.session.commit()
    return jsonify(budget.to_dict()), 200

#delete the budget
@budgets_bp.delete("/<int:budget_id>")
@jwt_required()
def delete_budget(budget_id):
    user_id = int(get_jwt_identity())
    # filter_by(..., user_id=user_id) here is what stops one user from
    # deleting another user's budget just by guessing its id.
    budget = Budget.query.filter_by(id=budget_id, user_id=user_id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Budget removed."}), 200
