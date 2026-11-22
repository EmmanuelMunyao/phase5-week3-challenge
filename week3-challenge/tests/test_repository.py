from pathlib import Path

import pytest

from repository import ReceiptStore


@pytest.fixture
def store(tmp_path):
    return ReceiptStore(tmp_path / "ghala.json")


def test_add_receipt(store):
    receipt = store.add_receipt({
        "farmer": "Kamau",
        "crop": "maize",
        "weight_kg": 100,
    })

    assert receipt["id"] == 1
    assert receipt["crop"] == "maize"
    assert receipt["weight_kg"] == 100


@pytest.mark.parametrize("weight", [0, -20])
def test_receipt_weight_must_be_positive(store, weight):
    with pytest.raises(ValueError, match="Weight must be greater than zero"):
        store.add_receipt({
            "farmer": "Wanjiru",
            "crop": "beans",
            "weight_kg": weight,
        })


def test_invalid_crop(store):
    with pytest.raises(ValueError, match="Invalid crop"):
        store.add_receipt({
            "farmer": "Wanjiru",
            "crop": "rice",
            "weight_kg": 50,
        })


def test_withdrawal_reduces_available_weight(store):
    receipt = store.add_receipt({
        "farmer": "Kamau",
        "crop": "maize",
        "weight_kg": 100,
    })

    store.add_withdrawal({
        "receipt_id": receipt["id"],
        "weight_kg": 60,
        "reason": "sale",
    })

    assert store.get_available_weight(receipt["id"]) == 40


def test_over_withdrawal_is_rejected(store):
    receipt = store.add_receipt({
        "farmer": "Kamau",
        "crop": "maize",
        "weight_kg": 100,
    })

    store.add_withdrawal({
        "receipt_id": receipt["id"],
        "weight_kg": 60,
        "reason": "sale",
    })

    with pytest.raises(
        ValueError,
        match="Withdrawal exceeds available weight",
    ):
        store.add_withdrawal({
            "receipt_id": receipt["id"],
            "weight_kg": 50,
            "reason": "sale",
        })


@pytest.mark.parametrize("weight", [0, -10])
def test_withdrawal_weight_must_be_positive(store, weight):
    receipt = store.add_receipt({
        "farmer": "Otieno",
        "crop": "wheat",
        "weight_kg": 100,
    })

    with pytest.raises(ValueError, match="Weight must be greater than zero"):
        store.add_withdrawal({
            "receipt_id": receipt["id"],
            "weight_kg": weight,
            "reason": "sale",
        })


def test_withdrawal_for_missing_receipt_is_rejected(store):
    with pytest.raises(ValueError, match="Receipt not found"):
        store.add_withdrawal({
            "receipt_id": 999,
            "weight_kg": 10,
            "reason": "sale",
        })