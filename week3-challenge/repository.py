from pathlib import Path
import json

from settings import load_settings


CROPS = ["maize", "beans", "wheat", "sorghum"]


class ReceiptStore:
    def __init__(self, data_file: Path):
        self.data_file = Path(data_file)

    def load(self):
        if not self.data_file.exists():
            return {
                "next_id": 1,
                "crops": CROPS.copy(),
                "receipts": [],
                "withdrawals": [],
            }

        with self.data_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self, data):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        with self.data_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def add_receipt(self, receipt):
        receipt = receipt.copy()

        if receipt["weight_kg"] <= 0:
            raise ValueError("Weight must be greater than zero")

        if receipt["crop"] not in CROPS:
            raise ValueError("Invalid crop")

        data = self.load()

        receipt["id"] = data["next_id"]
        data["next_id"] += 1

        data["receipts"].append(receipt)

        self.save(data)

        return receipt

    def get_receipt(self, receipt_id):
        data = self.load()

        for receipt in data["receipts"]:
            if receipt["id"] == receipt_id:
                return receipt

        return None

    def list_receipts(self):
        data = self.load()
        return data["receipts"]

    def get_available_weight(self, receipt_id):
        receipt = self.get_receipt(receipt_id)

        if receipt is None:
            return None

        data = self.load()

        withdrawn = sum(
            withdrawal["weight_kg"]
            for withdrawal in data["withdrawals"]
            if withdrawal["receipt_id"] == receipt_id
        )

        return receipt["weight_kg"] - withdrawn

    def add_withdrawal(self, withdrawal):
        withdrawal = withdrawal.copy()

        if withdrawal["weight_kg"] <= 0:
            raise ValueError("Weight must be greater than zero")

        receipt_id = withdrawal["receipt_id"]
        weight_kg = withdrawal["weight_kg"]

        available = self.get_available_weight(receipt_id)

        if available is None:
            raise ValueError("Receipt not found")

        if weight_kg > available:
            raise ValueError("Withdrawal exceeds available weight")

        data = self.load()

        withdrawal["id"] = data["next_id"]
        data["next_id"] += 1

        data["withdrawals"].append(withdrawal)

        self.save(data)

        return withdrawal

    def list_withdrawals(self):
        data = self.load()
        return data["withdrawals"]


# --------------------------------------------------
# Shared store
# --------------------------------------------------

_store = ReceiptStore(load_settings()["DATA_FILE"])


# --------------------------------------------------
# Receipt functions
# --------------------------------------------------

def add_receipt(receipt):
    return _store.add_receipt(receipt)


def get_receipts():
    return _store.list_receipts()


# --------------------------------------------------
# Withdrawal functions
# --------------------------------------------------

def add_withdrawal(withdrawal):
    return _store.add_withdrawal(withdrawal)


def get_withdrawals():
    return _store.list_withdrawals()


def get_available_weight(receipt_id):
    return _store.get_available_weight(receipt_id)