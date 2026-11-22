import pytest


def test_create_withdrawal(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 20,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["receipt_id"] == 1
    assert data["bags"] == 20
    assert data["taken_on"] == "2026-10-12"
    assert data["collected_by"] == "Barasa Makokha"
    assert data["fee_ksh"] == 20 * 25 * 3


def test_withdrawal_reduces_bags_left(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 20,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 201

    response = client.get("/api/receipts/1")

    assert response.status_code == 200
    assert response.get_json()["bags_left"] == 100


def test_over_withdrawal_returns_409(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 1000,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 409


def test_withdrawal_before_deposit_returns_409(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "taken_on": "2026-07-01",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 409


def test_get_receipt_withdrawals(client):
    response = client.get("/api/receipts/1/withdrawals")

    assert response.status_code == 200

    data = response.get_json()

    assert "items" in data


def test_get_missing_withdrawal_returns_404(client):
    response = client.get("/api/receipts/1/withdrawals/999")

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "Withdrawal not found"
    }


def test_missing_receipt_returns_404(client):
    response = client.post(
        "/api/receipts/999/withdrawals",
        json={
            "bags": 10,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "Receipt not found"
    }


@pytest.mark.parametrize("bags", [0, -1])
def test_invalid_bags_returns_400(client, bags):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": bags,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Invalid input."
    assert "details" in data


def test_invalid_bags_type_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": "twenty",
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Invalid input."
    assert data["details"] == [
        {
            "field": "bags",
            "message": "Bags must be greater than zero.",
        }
    ]


def test_missing_bags_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Invalid input.",
        "details": [
            {
                "field": "bags",
                "message": "Bags must be greater than zero.",
            }
        ],
    }


def test_missing_taken_on_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Invalid input.",
        "details": [
            {
                "field": "taken_on",
                "message": "Field is required.",
            }
        ],
    }


def test_invalid_taken_on_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "taken_on": "not-a-date",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Invalid input.",
        "details": [
            {
                "field": "taken_on",
                "message": "Invalid date.",
            }
        ],
    }


def test_future_withdrawal_date_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "taken_on": "2026-10-21",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 400

    assert response.get_json()["details"] == [
        {
            "field": "taken_on",
            "message": "A day cannot be after today.",
        }
    ]


def test_missing_collected_by_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "taken_on": "2026-10-12",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Invalid input.",
        "details": [
            {
                "field": "collected_by",
                "message": "Field is required.",
            }
        ],
    }


def test_non_json_withdrawal_returns_415(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        data="bags=10",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 415

    assert response.get_json() == {
        "error": "Send JSON with Content-Type: application/json."
    }


def test_non_object_json_withdrawal_returns_400(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json=["not", "an", "object"],
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Request body must be a JSON object"
    }


def test_list_missing_receipt_withdrawals_returns_404(client):
    response = client.get(
        "/api/receipts/999/withdrawals"
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "Receipt not found"
    }


def test_get_existing_withdrawal(client):
    response = client.post(
        "/api/receipts/1/withdrawals",
        json={
            "bags": 10,
            "taken_on": "2026-10-12",
            "collected_by": "Barasa Makokha",
        },
    )

    assert response.status_code == 201

    withdrawal = response.get_json()
    withdrawal_n = withdrawal["n"]

    response = client.get(
        f"/api/receipts/1/withdrawals/{withdrawal_n}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["n"] == withdrawal_n
    assert data["receipt_id"] == 1


def test_get_missing_receipt_withdrawal_returns_404(client):
    response = client.get(
        "/api/receipts/999/withdrawals/1"
    )

    assert response.status_code == 404

    assert response.get_json() == {
        "error": "Receipt not found"
    }


def test_list_flat_withdrawals_endpoint(client):
    response = client.get("/api/withdrawals")

    assert response.status_code == 200

    data = response.get_json()

    assert "items" in data