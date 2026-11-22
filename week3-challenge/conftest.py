import pytest

import repository
from app import app
from repository import ReceiptStore


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_file = tmp_path / "ghala.json"

    store = ReceiptStore(test_file)

    store.add_receipt({
        "farmer": "Kamau",
        "phone": "0712345678",
        "crop": "maize",
        "bags": 120,
        "moisture": 12,
        "deposited_on": "2026-10-09",
    })

    monkeypatch.setattr(
        repository,
        "_store",
        store,
    )

    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client
