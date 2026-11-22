from pathlib import Path
import json
import os

from settings import load_settings


CROPS = {"maize", "beans", "wheat", "sorghum"}


class ReceiptNotFound(Exception):
    pass


class WithdrawalNotFound(Exception):
    pass


class UnknownCrop(Exception):
    pass


class NotEnoughBags(Exception):
    pass


class TooEarly(Exception):
    pass


class ReceiptHasWithdrawals(Exception):
    pass


class DamagedStore(Exception):
    pass


class ReceiptStore:
    def __init__(self, data_file: Path):
        self.data_file = Path(data_file)

        # If the file already exists, validate it immediately.
        if self.data_file.exists():
            self.load()

    # ---------------------------------------------------------
    # STORAGE
    # ---------------------------------------------------------

    def load(self):
        if not self.data_file.exists():
            return {
                "next_id": 1,
                "receipts": [],
                "withdrawals": [],
            }

        try:
            with self.data_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError) as exc:
            raise DamagedStore(
                f"Could not read data store: {self.data_file}"
            ) from exc

        if not isinstance(data, dict):
            raise DamagedStore(
                "Data store must contain a JSON object"
            )

        if "receipts" not in data:
            data["receipts"] = []

        if "withdrawals" not in data:
            data["withdrawals"] = []

        if "next_id" not in data:
            data["next_id"] = self._calculate_next_id(data)

        return data

    def save(self, data):
        self.data_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_file = self.data_file.with_suffix(
            self.data_file.suffix + ".tmp"
        )

        try:
            with temp_file.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                )
                file.flush()
                os.fsync(file.fileno())

            os.replace(
                temp_file,
                self.data_file,
            )

        except OSError as exc:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

            raise DamagedStore(
                f"Could not save data store: {self.data_file}"
            ) from exc

    @staticmethod
    def _calculate_next_id(data):
        ids = []

        for receipt in data.get("receipts", []):
            if isinstance(receipt, dict) and isinstance(
                receipt.get("id"), int
            ):
                ids.append(receipt["id"])

        for withdrawal in data.get("withdrawals", []):
            if isinstance(withdrawal, dict) and isinstance(
                withdrawal.get("id"), int
            ):
                ids.append(withdrawal["id"])

        return max(ids, default=0) + 1

    # ---------------------------------------------------------
    # RECEIPTS
    # ---------------------------------------------------------

    def add_receipt(self, receipt):
        if not isinstance(receipt, dict):
            raise TypeError("Receipt must be an object")

        receipt = receipt.copy()

        crop = receipt.get("crop")

        if crop not in CROPS:
            raise UnknownCrop(crop)

        # The challenge uses bags, while some of the older API
        # tests use weight_kg. Support both.
        bags = receipt.get("bags")

        if bags is None:
            weight_kg = receipt.get("weight_kg")

            if weight_kg is not None:
                bags = weight_kg

        if bags is None:
            raise ValueError("Bags must be greater than zero")

        try:
            if bags <= 0:
                raise ValueError(
                    "Bags must be greater than zero"
                )
        except TypeError as exc:
            raise ValueError(
                "Bags must be greater than zero"
            ) from exc

        data = self.load()

        receipt["id"] = data["next_id"]
        data["next_id"] += 1

        receipt["bags"] = bags
        receipt["bags_left"] = bags

        # Preserve weight_kg when supplied.
        if "weight_kg" in receipt:
            receipt["weight_kg"] = receipt["weight_kg"]

        data.setdefault("receipts", [])
        data.setdefault("withdrawals", [])

        data["receipts"].append(receipt)

        self.save(data)

        return receipt

    def get(self, receipt_id):
        data = self.load()

        for receipt in data["receipts"]:
            if receipt["id"] == receipt_id:
                return receipt

        raise ReceiptNotFound(receipt_id)

    def all(self):
        data = self.load()
        return data["receipts"]

    def update(self, receipt_id, changes):
        if not isinstance(changes, dict):
            raise TypeError("Changes must be an object")

        data = self.load()

        receipt = None

        for item in data["receipts"]:
            if item["id"] == receipt_id:
                receipt = item
                break

        if receipt is None:
            raise ReceiptNotFound(receipt_id)

        changes = changes.copy()

        # Validate crop if it is being changed.
        if "crop" in changes:
            if changes["crop"] not in CROPS:
                raise UnknownCrop(changes["crop"])

        # Support both bags and weight_kg.
        if "bags" in changes:
            new_bags = changes["bags"]

        elif "weight_kg" in changes:
            new_bags = changes["weight_kg"]

        else:
            new_bags = None

        if new_bags is not None:
            try:
                if new_bags <= 0:
                    raise ValueError(
                        "Bags must be greater than zero"
                    )
            except TypeError as exc:
                raise ValueError(
                    "Bags must be greater than zero"
                ) from exc

            withdrawn = sum(
                withdrawal["bags"]
                for withdrawal in data["withdrawals"]
                if withdrawal["receipt_id"] == receipt_id
            )

            if new_bags < withdrawn:
                raise NotEnoughBags(
                    "Receipt bags cannot be below withdrawn amount"
                )

            changes["bags"] = new_bags

            if "weight_kg" in changes:
                changes["weight_kg"] = new_bags

        receipt.update(changes)

        withdrawn = sum(
            withdrawal["bags"]
            for withdrawal in data["withdrawals"]
            if withdrawal["receipt_id"] == receipt_id
        )

        receipt["bags_left"] = receipt["bags"] - withdrawn

        self.save(data)

        return receipt

    def delete(self, receipt_id):
        data = self.load()

        receipt = None

        for item in data["receipts"]:
            if item["id"] == receipt_id:
                receipt = item
                break

        if receipt is None:
            raise ReceiptNotFound(receipt_id)

        has_withdrawals = any(
            withdrawal["receipt_id"] == receipt_id
            for withdrawal in data["withdrawals"]
        )

        if has_withdrawals:
            raise ReceiptHasWithdrawals(receipt_id)

        data["receipts"].remove(receipt)

        self.save(data)

        return receipt

    # ---------------------------------------------------------
    # WITHDRAWALS
    # ---------------------------------------------------------

    def add_withdrawal(self, receipt_id, withdrawal):
        if not isinstance(withdrawal, dict):
            raise TypeError("Withdrawal must be an object")

        withdrawal = withdrawal.copy()

        # First verify the receipt exists.
        receipt = self.get(receipt_id)

        bags = withdrawal.get("bags")

        try:
            if bags is None or bags <= 0:
                raise ValueError(
                    "Bags must be greater than zero"
                )
        except TypeError as exc:
            raise ValueError(
                "Bags must be greater than zero"
            ) from exc

        taken_on = withdrawal.get("taken_on")
        deposited_on = receipt.get("deposited_on")

        if (
            taken_on is not None
            and deposited_on is not None
            and taken_on < deposited_on
        ):
            raise TooEarly(
                "Withdrawal cannot happen before deposit"
            )

        data = self.load()

        existing_withdrawals = [
            item
            for item in data["withdrawals"]
            if item["receipt_id"] == receipt_id
        ]

        withdrawn = sum(
            item["bags"]
            for item in existing_withdrawals
        )

        available = receipt["bags"] - withdrawn

        if bags > available:
            raise NotEnoughBags(
                "Withdrawal exceeds available bags"
            )

        previous_numbers = [
            item.get("n", 0)
            for item in existing_withdrawals
        ]

        next_n = max(
            previous_numbers,
            default=0,
        ) + 1

        withdrawal["n"] = next_n
        withdrawal["receipt_id"] = receipt_id

        # Give every withdrawal its own ID.
        withdrawal["id"] = data["next_id"]
        data["next_id"] += 1

        # Calculate storage days and fee when possible.
        if taken_on is not None and deposited_on is not None:
            try:
                from datetime import date

                deposit_date = date.fromisoformat(
                    deposited_on
                )
                withdrawal_date = date.fromisoformat(
                    taken_on
                )

                storage_days = (
                    withdrawal_date - deposit_date
                ).days

                # Minimum one day of storage.
                storage_days = max(storage_days, 1)

                fee = (
                    bags
                    * load_settings()["STORAGE_FEE_KSH"]
                    * storage_days
                )

                withdrawal["fee_ksh"] = fee

            except (ValueError, TypeError):
                pass

        data["withdrawals"].append(withdrawal)

        # Update receipt balance.
        for item in data["receipts"]:
            if item["id"] == receipt_id:
                item["bags_left"] = available - bags
                break

        self.save(data)

        return withdrawal

    def withdrawals(self, receipt_id):
        # Ensure receipt exists.
        self.get(receipt_id)

        data = self.load()

        return [
            withdrawal
            for withdrawal in data["withdrawals"]
            if withdrawal["receipt_id"] == receipt_id
        ]

    def withdrawal(self, receipt_id, n):
        withdrawals = self.withdrawals(receipt_id)

        for withdrawal in withdrawals:
            if (
                withdrawal.get("n") == n
                or withdrawal.get("id") == n
            ):
                return withdrawal

        raise WithdrawalNotFound(
            f"Withdrawal {n} not found"
        )


# -------------------------------------------------------------
# GLOBAL STORE
# -------------------------------------------------------------

_store = ReceiptStore(
    load_settings()["DATA_FILE"]
)


# -------------------------------------------------------------
# RECEIPT HELPERS
# -------------------------------------------------------------

def add_receipt(receipt):
    return _store.add_receipt(receipt)


def get_receipts():
    return _store.all()


def get_receipt(receipt_id):
    return _store.get(receipt_id)


def update_receipt(receipt_id, changes):
    return _store.update(
        receipt_id,
        changes,
    )


def delete_receipt(receipt_id):
    return _store.delete(receipt_id)


# -------------------------------------------------------------
# WITHDRAWAL HELPERS
# -------------------------------------------------------------

def add_withdrawal(receipt_id, withdrawal):
    return _store.add_withdrawal(
        receipt_id,
        withdrawal,
    )


def get_withdrawals(receipt_id=None):
    if receipt_id is None:
        data = _store.load()
        return data["withdrawals"]

    return _store.withdrawals(receipt_id)


def get_withdrawal(receipt_id, n):
    return _store.withdrawal(
        receipt_id,
        n,
    )


def get_available_bags(receipt_id):
    receipt = _store.get(receipt_id)
    return receipt["bags_left"]