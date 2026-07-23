from flask import Blueprint, jsonify
from models import Category

#create blueprint
categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")

#get Categories list
@categories_bp.get("")
def list_categories():
    categories = Category.query.order_by(Category.id).all()
    #convert to json
    return jsonify([c.to_dict() for c in categories]), 200