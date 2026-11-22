from flask import Blueprint, jsonify, request

from repository import add_receipt, get_receipts


receipts_bp = Blueprint("receipts", __name__)


@receipts_bp.get("/api/receipts")
def list_receipts():
    return jsonify({
        "items": get_receipts(),
    })


@receipts_bp.post("/api/receipts")
def create_receipt():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    try:
        receipt = add_receipt(data)

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(receipt), 201