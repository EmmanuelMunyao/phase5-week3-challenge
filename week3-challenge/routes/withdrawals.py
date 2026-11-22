from flask import Blueprint, jsonify, request

from repository import add_withdrawal, get_withdrawals


withdrawals_bp = Blueprint("withdrawals", __name__)


@withdrawals_bp.get("/api/withdrawals")
def list_withdrawals():
    return jsonify({
        "items": get_withdrawals(),
    })


@withdrawals_bp.post("/api/withdrawals")
def create_withdrawal():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    try:
        withdrawal = add_withdrawal(data)

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(withdrawal), 201