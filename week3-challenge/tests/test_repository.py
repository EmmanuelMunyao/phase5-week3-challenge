import json

import pytest

from repository import (
    CROPS,
    DamagedStore,
    NotEnoughBags,
    ReceiptHasWithdrawals,
    ReceiptNotFound,
    ReceiptStore,
    TooEarly,
    UnknownCrop,
    WithdrawalNotFound,
)


@pytest.fixture
def store(tmp_path):
    return ReceiptStore(tmp_path / "ghala.json")


def receipt_data(**overrides):
    data = {
        "farmer": "Kamau",
        "phone": "0712345678",
        "crop": "maize",
        "bags": 100,
        "moisture": 10.5,
        "deposited_on": "2026-10-01",
    }
    data.update(overrides)
    return data


def withdrawal_data(**overrides):
    data = {
        "bags": 20,
        "taken_on": "2026-10-12",
        "collected_by": "Barasa Makokha",
    }
    data.update(overrides)
    return data


def test_crops_are_defined():
    assert CROPS == {"maize", "beans", "wheat", "sorghum"}


def test_add_receipt(store):
    receipt = store.add_receipt(receipt_data())

    assert receipt["id"] == 1
    assert receipt["farmer"] == "Kamau"
    assert receipt["phone"] == "0712345678"
    assert receipt["crop"] == "maize"
    assert receipt["bags"] == 100
    assert receipt["moisture"] == 10.5
    assert receipt["deposited_on"] == "2026-10-01"
    assert receipt["bags_left"] == 100


def test_receipt_ids_increment(store):
    first = store.add_receipt(receipt_data())

    second = store.add_receipt(
        receipt_data(
            farmer="Wanjiru",
            phone="0722222222",
            crop="beans",
        )
    )

    assert first["id"] == 1
    assert second["id"] == 2


def test_unknown_crop_is_rejected(store):
    with pytest.raises(UnknownCrop):
        store.add_receipt(receipt_data(crop="rice"))


def test_get_receipt(store):
    created = store.add_receipt(receipt_data())

    found = store.get(created["id"])

    assert found["id"] == created["id"]
    assert found["bags"] == 100


def test_missing_receipt_is_rejected(store):
    with pytest.raises(ReceiptNotFound):
        store.get(999)


def test_all_receipts(store):
    store.add_receipt(receipt_data())

    store.add_receipt(
        receipt_data(
            farmer="Wanjiru",
            phone="0722222222",
            crop="beans",
        )
    )

    receipts = store.all()

    assert len(receipts) == 2
    assert receipts[0]["id"] == 1
    assert receipts[1]["id"] == 2


def test_update_receipt(store):
    created = store.add_receipt(receipt_data())

    updated = store.update(
        created["id"],
        {
            "farmer": "Wanjiru",
            "bags": 150,
        },
    )

    assert updated["farmer"] == "Wanjiru"
    assert updated["bags"] == 150
    assert updated["bags_left"] == 150


def test_update_missing_receipt_is_rejected(store):
    with pytest.raises(ReceiptNotFound):
        store.update(999, {"bags": 50})


def test_delete_receipt(store):
    created = store.add_receipt(receipt_data())

    store.delete(created["id"])

    with pytest.raises(ReceiptNotFound):
        store.get(created["id"])


def test_withdrawal_reduces_bags_left(store):
    receipt = store.add_receipt(receipt_data())

    withdrawal = store.add_withdrawal(
        receipt["id"],
        withdrawal_data(),
    )

    assert withdrawal["bags"] == 20

    updated = store.get(receipt["id"])

    assert updated["bags_left"] == 80


def test_over_withdrawal_is_rejected(store):
    receipt = store.add_receipt(receipt_data(bags=100))

    with pytest.raises(NotEnoughBags):
        store.add_withdrawal(
            receipt["id"],
            withdrawal_data(bags=101),
        )


def test_withdrawal_before_deposit_is_rejected(store):
    receipt = store.add_receipt(
        receipt_data(deposited_on="2026-10-10")
    )

    with pytest.raises(TooEarly):
        store.add_withdrawal(
            receipt["id"],
            withdrawal_data(taken_on="2026-10-09"),
        )


def test_withdrawal_missing_receipt_is_rejected(store):
    with pytest.raises(ReceiptNotFound):
        store.add_withdrawal(
            999,
            withdrawal_data(),
        )


def test_get_withdrawals(store):
    receipt = store.add_receipt(receipt_data())

    store.add_withdrawal(
        receipt["id"],
        withdrawal_data(bags=10),
    )

    store.add_withdrawal(
        receipt["id"],
        withdrawal_data(
            bags=20,
            taken_on="2026-10-13",
        ),
    )

    withdrawals = store.withdrawals(receipt["id"])

    assert len(withdrawals) == 2
    assert withdrawals[0]["n"] == 1
    assert withdrawals[1]["n"] == 2


def test_get_one_withdrawal(store):
    receipt = store.add_receipt(receipt_data())

    created = store.add_withdrawal(
        receipt["id"],
        withdrawal_data(),
    )

    found = store.withdrawal(
        receipt["id"],
        created["n"],
    )

    assert found["n"] == created["n"]
    assert found["receipt_id"] == receipt["id"]


def test_missing_withdrawal_is_rejected(store):
    receipt = store.add_receipt(receipt_data())

    with pytest.raises(WithdrawalNotFound):
        store.withdrawal(receipt["id"], 999)


def test_delete_receipt_with_withdrawals_is_rejected(store):
    receipt = store.add_receipt(receipt_data())

    store.add_withdrawal(
        receipt["id"],
        withdrawal_data(),
    )

    with pytest.raises(ReceiptHasWithdrawals):
        store.delete(receipt["id"])


def test_update_cannot_reduce_bags_below_withdrawn_amount(store):
    receipt = store.add_receipt(
        receipt_data(bags=100)
    )

    store.add_withdrawal(
        receipt["id"],
        withdrawal_data(bags=40),
    )

    with pytest.raises(NotEnoughBags):
        store.update(
            receipt["id"],
            {"bags": 30},
        )


def test_data_survives_new_store_instance(store, tmp_path):
    created = store.add_receipt(receipt_data())

    store.add_withdrawal(
        created["id"],
        withdrawal_data(),
    )

    new_store = ReceiptStore(
        tmp_path / "ghala.json"
    )

    receipt = new_store.get(created["id"])

    assert receipt["bags"] == 100
    assert receipt["bags_left"] == 80
    assert len(
        new_store.withdrawals(created["id"])
    ) == 1


def test_damaged_json_raises_damaged_store(tmp_path):
    path = tmp_path / "ghala.json"

    path.write_text(
        "{this is not valid json",
        encoding="utf-8",
    )

    with pytest.raises(DamagedStore):
        ReceiptStore(path)


def test_repository_writes_valid_json(store, tmp_path):
    store.add_receipt(receipt_data())

    path = tmp_path / "ghala.json"

    raw = path.read_text(
        encoding="utf-8"
    )

    data = json.loads(raw)

    assert isinstance(data, dict)


# =========================================================
# ADDITIONAL COVERAGE TESTS
# =========================================================


def test_load_missing_file_returns_empty_store(tmp_path):
    store = ReceiptStore(
        tmp_path / "missing.json"
    )

    data = store.load()

    assert data == {
        "next_id": 1,
        "receipts": [],
        "withdrawals": [],
    }


def test_load_non_dict_json_raises_damaged_store(tmp_path):
    path = tmp_path / "ghala.json"

    path.write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(DamagedStore):
        ReceiptStore(path)


def test_load_adds_missing_collections_and_next_id(tmp_path):
    path = tmp_path / "ghala.json"

    path.write_text(
        json.dumps(
            {
                "receipts": [
                    {
                        "id": 4,
                        "bags": 50,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    store = ReceiptStore(path)

    data = store.load()

    assert data["receipts"] == [
        {
            "id": 4,
            "bags": 50,
        }
    ]

    assert data["withdrawals"] == []
    assert data["next_id"] == 5


def test_add_receipt_rejects_non_dict(store):
    with pytest.raises(TypeError):
        store.add_receipt([])


def test_add_receipt_requires_positive_bags(store):
    with pytest.raises(ValueError):
        store.add_receipt(
            receipt_data(bags=0)
        )

    with pytest.raises(ValueError):
        store.add_receipt(
            receipt_data(bags=-1)
        )


def test_add_receipt_rejects_invalid_bags_type(store):
    with pytest.raises(ValueError):
        store.add_receipt(
            receipt_data(bags="many")
        )


def test_update_rejects_non_dict(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(TypeError):
        store.update(
            receipt["id"],
            [],
        )


def test_update_rejects_unknown_crop(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(UnknownCrop):
        store.update(
            receipt["id"],
            {"crop": "rice"},
        )


def test_update_rejects_invalid_bags(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(ValueError):
        store.update(
            receipt["id"],
            {"bags": 0},
        )

    with pytest.raises(ValueError):
        store.update(
            receipt["id"],
            {"bags": "many"},
        )


def test_delete_missing_receipt_is_rejected(store):
    with pytest.raises(ReceiptNotFound):
        store.delete(999)


def test_add_withdrawal_rejects_non_dict(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(TypeError):
        store.add_withdrawal(
            receipt["id"],
            [],
        )


def test_add_withdrawal_requires_positive_bags(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(ValueError):
        store.add_withdrawal(
            receipt["id"],
            withdrawal_data(bags=0),
        )

    with pytest.raises(ValueError):
        store.add_withdrawal(
            receipt["id"],
            withdrawal_data(bags=-1),
        )


def test_add_withdrawal_rejects_invalid_bags_type(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    with pytest.raises(ValueError):
        store.add_withdrawal(
            receipt["id"],
            withdrawal_data(bags="many"),
        )


def test_withdrawal_fee_is_calculated(store):
    receipt = store.add_receipt(
        receipt_data(
            deposited_on="2026-10-01"
        )
    )

    withdrawal = store.add_withdrawal(
        receipt["id"],
        withdrawal_data(
            bags=10,
            taken_on="2026-10-11",
        ),
    )

    assert "fee_ksh" in withdrawal
    assert withdrawal["fee_ksh"] > 0


def test_withdrawal_with_invalid_dates_does_not_fail(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    withdrawal = store.add_withdrawal(
        receipt["id"],
        withdrawal_data(
            taken_on="not-a-date"
        ),
    )

    assert withdrawal["bags"] == 20
    assert "fee_ksh" not in withdrawal


def test_get_all_withdrawals(store):
    receipt = store.add_receipt(
        receipt_data()
    )

    store.add_withdrawal(
        receipt["id"],
        withdrawal_data(),
    )

    withdrawals = store.withdrawals(
        receipt["id"]
    )

    assert len(withdrawals) == 1