from flask import Blueprint, jsonify

from repository import CROPS


crops_bp = Blueprint("crops", __name__)


@crops_bp.get("/api/crops")
def list_crops():
    return jsonify({
        "items": CROPS,
    })