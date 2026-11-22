import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_get_receipts(client):
    response = client.get("/api/receipts")

    assert response.status_code == 200

    data = response.get_json()

    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_receipt(client):
    response = client.post(
        "/api/receipts",
        json={
            "farmer": "Kamau",
            "crop": "maize",
            "weight_kg": 100,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["farmer"] == "Kamau"
    assert data["crop"] == "maize"
    assert data["weight_kg"] == 100
    assert "id" in data


def test_create_receipt_requires_json_object(client):
    response = client.post(
        "/api/receipts",
        json=[],
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Request body must be a JSON object"
    }


@pytest.mark.parametrize("weight", [0, -10])
def test_create_receipt_rejects_invalid_weight(client, weight):
    response = client.post(
        "/api/receipts",
        json={
            "farmer": "Wanjiru",
            "crop": "beans",
            "weight_kg": weight,
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Weight must be greater than zero"
    }


def test_create_receipt_rejects_invalid_crop(client):
    response = client.post(
        "/api/receipts",
        json={
            "farmer": "Otieno",
            "crop": "rice",
            "weight_kg": 50,
        },
    )

    assert response.status_code == 400

    assert response.get_json() == {
        "error": "Invalid crop"
    }