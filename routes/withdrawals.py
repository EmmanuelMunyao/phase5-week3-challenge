from datetime import date

from flask import Blueprint, jsonify, request

from repository import (
    NotEnoughBags,
    ReceiptNotFound,
    TooEarly,
    WithdrawalNotFound,
    add_withdrawal,
    get_withdrawal,
    get_withdrawals,
)


withdrawals_bp = Blueprint("withdrawals", __name__)


def validation_error(field, message):
    return jsonify({
        "error": "Invalid input.",
        "details": [
            {
                "field": field,
                "message": message,
            }
        ],
    }), 400


@withdrawals_bp.post(
    "/api/receipts/<int:receipt_id>/withdrawals"
)
def create_receipt_withdrawal(receipt_id):
    # Flask should return 415 for non-JSON requests.
    if not request.is_json:
        return jsonify({
            "error": (
                "Send JSON with Content-Type: "
                "application/json."
            )
        }), 415

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    bags = data.get("bags")

    try:
        if bags is None or bags <= 0:
            return validation_error(
                "bags",
                "Bags must be greater than zero.",
            )
    except TypeError:
        return validation_error(
            "bags",
            "Bags must be greater than zero.",
        )

    taken_on = data.get("taken_on")

    if not taken_on:
        return validation_error(
            "taken_on",
            "Field is required.",
        )

    try:
        taken_date = date.fromisoformat(taken_on)
    except (ValueError, TypeError):
        return validation_error(
            "taken_on",
            "Invalid date.",
        )

    # Challenge's current date is 2026-10-20.
    today = date(2026, 10, 20)

    if taken_date > today:
        return jsonify({
            "error": "Invalid input.",
            "details": [
                {
                    "field": "taken_on",
                    "message": "A day cannot be after today.",
                }
            ],
        }), 400

    if not data.get("collected_by"):
        return validation_error(
            "collected_by",
            "Field is required.",
        )

    try:
        withdrawal = add_withdrawal(
            receipt_id,
            data,
        )

    except ReceiptNotFound:
        return jsonify({
            "error": "Receipt not found"
        }), 404

    except TooEarly as exc:
        return jsonify({
            "error": str(exc)
        }), 409

    except NotEnoughBags as exc:
        return jsonify({
            "error": str(exc)
        }), 409

    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    return jsonify(withdrawal), 201


@withdrawals_bp.get(
    "/api/receipts/<int:receipt_id>/withdrawals"
)
def list_receipt_withdrawals(receipt_id):
    try:
        withdrawals = get_withdrawals(receipt_id)

    except ReceiptNotFound:
        return jsonify({
            "error": "Receipt not found"
        }), 404

    return jsonify({
        "items": withdrawals,
    })


@withdrawals_bp.get(
    "/api/receipts/<int:receipt_id>/withdrawals/<int:n>"
)
def get_receipt_withdrawal(receipt_id, n):
    try:
        withdrawal = get_withdrawal(
            receipt_id,
            n,
        )

    except ReceiptNotFound:
        return jsonify({
            "error": "Receipt not found"
        }), 404

    except WithdrawalNotFound:
        return jsonify({
            "error": "Withdrawal not found"
        }), 404

    return jsonify(withdrawal)


# Keep the old flat endpoint available.
@withdrawals_bp.get("/api/withdrawals")
def list_withdrawals():
    return jsonify({
        "items": get_withdrawals(),
    })
