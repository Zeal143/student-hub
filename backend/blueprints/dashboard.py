from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from extensions import db
from models import User, Expense, SavingsGoal, BinSchedule
from blueprints.bins import _next_occurrences  
from blueprints.budgets import budgets_with_spent

# Create Blueprint
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# Dashboard route
@dashboard_bp.get("")
# Right user can access
@jwt_required()
def dashboard():

	#get current user
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    #get current date
    now = datetime.utcnow()
    
    #get recent expenses
    recent_expenses = (
        Expense.query.filter_by(user_id=user_id)
        .order_by(Expense.date.desc())
        .limit(5)
        .all()
    )
    #get total spent of this month
    total_spent_this_month = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == user_id,
            func.extract("year", Expense.date) == now.year,
            func.extract("month", Expense.date) == now.month,
        )
        .scalar()
    )
    #get budget
    budgets = budgets_with_spent(user_id)
    #get savaings goals
    savings_goals = SavingsGoal.query.filter_by(user_id=user_id).all()

    # Bin collections (only appear once the user has set an Eircode + provider)
    bin_collections = []
    if user.eircode and user.bin_provider_id:
        eircode_prefix = user.eircode.replace(" ", "")[:3]
        schedules = BinSchedule.query.filter_by(
            eircode_prefix=eircode_prefix, provider_id=user.bin_provider_id
        ).all()
        for s in schedules:
            # Only the next occurrence of each schedule row is needed here
            next_date = _next_occurrences(s.collection_weekday, s.frequency_weeks, count=1)[0]
            bin_collections.append({**s.to_dict(), "collection_date": next_date.isoformat()})
        bin_collections.sort(key=lambda row: row["collection_date"])

    return jsonify({
        "user": user.to_dict(),
        "recent_expenses": [e.to_dict() for e in recent_expenses],
        "total_spent_this_month": float(total_spent_this_month),
        "budgets": budgets,  
        "savings_goals": [g.to_dict() for g in savings_goals],
        "upcoming_bin_collections": bin_collections[:3],  # cap at 3 so the dashboard card stays compact
        "has_bin_settings": bool(user.eircode and user.bin_provider_id),
    }), 200