from flask import Blueprint, jsonify, request

from repository import (
    ReceiptNotFound,
    UnknownCrop,
    add_receipt,
    get_receipt,
    get_receipts,
)

receipts_bp = Blueprint("receipts", __name__)


@receipts_bp.get("/api/receipts")
def list_receipts():
    return jsonify({
        "items": get_receipts(),
    })


@receipts_bp.get("/api/receipts/<int:receipt_id>")
def get_single_receipt(receipt_id):
    try:
        receipt = get_receipt(receipt_id)

    except ReceiptNotFound:
        return jsonify({
            "error": "Receipt not found"
        }), 404

    return jsonify(receipt)


@receipts_bp.post("/api/receipts")
def create_receipt():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    if "weight_kg" in data:
        try:
            if data["weight_kg"] <= 0:
                return jsonify({
                    "error": "Weight must be greater than zero"
                }), 400
        except TypeError:
            return jsonify({
                "error": "Weight must be greater than zero"
            }), 400

    try:
        receipt = add_receipt(data)

    except UnknownCrop:
        return jsonify({
            "error": "Invalid crop"
        }), 400

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(receipt), 201