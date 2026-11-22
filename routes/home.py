from flask import Blueprint, jsonify


home_bp = Blueprint("home", __name__)


@home_bp.get("/")
def home():
    return jsonify({
        "name": "Ghala Moi's Bridge Warehouse",
        "status": "ok",
    })


@home_bp.get("/api/health")
def health():
    return jsonify({"status": "ok"})
