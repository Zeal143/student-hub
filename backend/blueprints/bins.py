import re
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, BinProvider, BinSchedule

bins_bp = Blueprint("bins", __name__, url_prefix="/api/bins")

# Very loose Eircode check(1 letter + 2 alphanumerics) 
EIRCODE_RE = re.compile(r"^[A-Za-z]\d[\dW]\s?[A-Za-z0-9]{4}$")

# Reference Monday used as the anchor for fortnightly ("every 2nd week")
_REFERENCE_MONDAY = date(2024, 1, 1)  # a Monday

#get all bin providers' list
@bins_bp.get("/providers")
def list_providers():
    providers = BinProvider.query.order_by(BinProvider.name).all()
    return jsonify([p.to_dict() for p in providers]), 200

# save user's eircode and provider 
@bins_bp.post("/settings")
@jwt_required()
def set_bin_settings():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    eircode = (data.get("eircode") or "").strip().upper()
    provider_id = data.get("provider_id")

    if not EIRCODE_RE.match(eircode):
        return jsonify({"error": "Please enter a valid Eircode, e.g. D02 AF30."}), 400
    if not BinProvider.query.get(provider_id):
        return jsonify({"error": "Please select a valid bin collection provider."}), 400

    eircode_prefix = eircode.replace(" ", "")[:3]
    if not BinSchedule.query.filter_by(eircode_prefix=eircode_prefix, provider_id=provider_id).first():
        return jsonify({
            "error": (
                "No schedule is currently available for that Eircode and provider "
                "combination. Please double-check your details or contact your provider."
            )
        }), 404

    user = User.query.get_or_404(user_id)
    user.eircode = eircode
    user.bin_provider_id = provider_id
    db.session.commit()

    return jsonify(user.to_dict()), 200

#function to calculate the next date
def _next_occurrences(collection_weekday, frequency_weeks, count=3, from_date=None):
    """Return the next `count` dates a given weekday/frequency schedule falls on."""
    today = from_date or date.today()

    days_ahead = (collection_weekday - today.weekday()) % 7
    next_date = today + timedelta(days=days_ahead)

    if frequency_weeks > 1:
        weeks_since_ref = (next_date - _REFERENCE_MONDAY).days // 7
        offset = weeks_since_ref % frequency_weeks
        if offset != 0:
            next_date += timedelta(weeks=(frequency_weeks - offset))

    occurrences = []
    current = next_date
    for _ in range(count):
        occurrences.append(current)
        current += timedelta(weeks=frequency_weeks)
    return occurrences

#get upcoming collection dates 
@bins_bp.get("/schedule")
@jwt_required()
def get_schedule():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if not user.eircode or not user.bin_provider_id:
        return jsonify({"error": "Please set your Eircode and provider first."}), 400

    eircode_prefix = user.eircode.replace(" ", "")[:3]
    schedules = BinSchedule.query.filter_by(
        eircode_prefix=eircode_prefix, provider_id=user.bin_provider_id
    ).all()

    if not schedules:
        return jsonify({"error": "No schedule found for your address."}), 404

    upcoming = []
    for s in schedules:
        for occurrence in _next_occurrences(s.collection_weekday, s.frequency_weeks, count=3):
            upcoming.append({**s.to_dict(), "collection_date": occurrence.isoformat()})

    upcoming.sort(key=lambda row: row["collection_date"])
    return jsonify(upcoming), 200
