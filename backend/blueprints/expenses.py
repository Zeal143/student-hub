
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from extensions import db
from models import Expense, Category

# Create Blueprint
expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")

# Convert the String into Date Object
def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


@expenses_bp.get("")
@jwt_required()
def list_expenses():
    user_id = int(get_jwt_identity())
    expenses = (
        Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    )
    return jsonify([e.to_dict() for e in expenses]), 200


@expenses_bp.post("")
@jwt_required()
def create_expense():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    try:
        amount = float(data.get("amount"))
        if amount <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a positive number."}), 400

    category_id = data.get("category_id")
    if not Category.query.get(category_id):
        return jsonify({"error": "Invalid category."}), 400

    try:
        date = _parse_date(data.get("date"))
    except (TypeError, ValueError):
        return jsonify({"error": "Date must be in YYYY-MM-DD format."}), 400

    expense = Expense(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        description=(data.get("description") or "").strip()[:255],
        date=date,
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify(expense.to_dict()), 201

#updating the existing expenses
@expenses_bp.put("/<int:expense_id>")
@jwt_required()
def update_expense(expense_id):
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first_or_404()
    data = request.get_json(silent=True) or {}

    if "amount" in data:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                raise ValueError
            expense.amount = amount
        except (TypeError, ValueError):
            return jsonify({"error": "Amount must be a positive number."}), 400

    if "category_id" in data:
        if not Category.query.get(data["category_id"]):
            return jsonify({"error": "Invalid category."}), 400
        expense.category_id = data["category_id"]

    if "date" in data:
        try:
            expense.date = _parse_date(data["date"])
        except (TypeError, ValueError):
            return jsonify({"error": "Date must be in YYYY-MM-DD format."}), 400

    if "description" in data:
        expense.description = (data["description"] or "").strip()[:255]

    db.session.commit()
    return jsonify(expense.to_dict()), 200

#Deleting the expenses
@expenses_bp.delete("/<int:expense_id>")
@jwt_required()
def delete_expense(expense_id):
    user_id = int(get_jwt_identity())
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted."}), 200

#Get the summary of expenses
@expenses_bp.get("/summary")
@jwt_required()
def spending_summary():
    #Aggregated spend by category for pie/bar charts, current calendar month.
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()

    rows = (
        db.session.query(Category.name, func.sum(Expense.amount))
        .join(Expense, Expense.category_id == Category.id)
        .filter(
            Expense.user_id == user_id,
            func.extract("year", Expense.date) == now.year,
            func.extract("month", Expense.date) == now.month,
        )
        .group_by(Category.name)
        .all()
    )
    return jsonify([{"category": name, "total": float(total)} for name, total in rows]), 200