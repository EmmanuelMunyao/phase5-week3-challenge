import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_get_withdrawals(client):
    response = client.get("/api/withdrawals")

    assert response.status_code == 200

    data = response.get_json()

    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_withdrawal(client):
    response = client.post(
        "/api/withdrawals",
        json={
            "receipt_id": 1,
            "weight_kg": 10,
            "reason": "sale",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["receipt_id"] == 1
    assert data["weight_kg"] == 10
    assert data["reason"] == "sale"
    assert "id" in data


def test_create_withdrawal_requires_json_object(client):
    response = client.post(
        "/api/withdrawals",
        json=[],
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Request body must be a JSON object"
    }


@pytest.mark.parametrize("weight", [0, -10])
def test_create_withdrawal_rejects_invalid_weight(client, weight):
    response = client.post(
        "/api/withdrawals",
        json={
            "receipt_id": 1,
            "weight_kg": weight,
            "reason": "sale",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Weight must be greater than zero"
    }


def test_create_withdrawal_rejects_missing_receipt(client):
    response = client.post(
        "/api/withdrawals",
        json={
            "receipt_id": 999999,
            "weight_kg": 10,
            "reason": "sale",
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Receipt not found"
    }