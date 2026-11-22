from pathlib import Path
import tempfile

from repository import ReceiptStore


store = ReceiptStore(
    Path(tempfile.mkdtemp()) / "ghala.json"
)


print("=== OVER-WITHDRAWAL TEST ===")

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

print("Available:", store.get_available_weight(receipt["id"]))

try:
    store.add_withdrawal({
        "receipt_id": receipt["id"],
        "weight_kg": 50,
        "reason": "sale",
    })

    print("ERROR: withdrawal was allowed")

except ValueError as error:
    print("Rejected:", error)

print("Available after:", store.get_available_weight(receipt["id"]))


print("\n=== INVALID RECEIPT WEIGHT TEST ===")

for weight in [0, -20]:
    try:
        store.add_receipt({
            "farmer": "Wanjiru",
            "crop": "beans",
            "weight_kg": weight,
        })

        print(f"ERROR: receipt with {weight} kg was accepted")

    except ValueError as error:
        print(f"Receipt {weight} kg rejected:", error)


print("\n=== INVALID WITHDRAWAL WEIGHT TEST ===")

valid_receipt = store.add_receipt({
    "farmer": "Otieno",
    "crop": "wheat",
    "weight_kg": 100,
})

for weight in [0, -10]:
    try:
        store.add_withdrawal({
            "receipt_id": valid_receipt["id"],
            "weight_kg": weight,
            "reason": "sale",
        })

        print(f"ERROR: withdrawal with {weight} kg was accepted")

    except ValueError as error:
        print(f"Withdrawal {weight} kg rejected:", error)