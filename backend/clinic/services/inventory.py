"""
Inventory integration boundary.

For the midterm implementation this service uses deterministic in-memory mock
data. Clinic never owns the medicine catalog, medicine stock, or Inventory
stock transactions.
"""

from copy import deepcopy


class MedicineNotFoundError(Exception):
    """Raised when Inventory does not contain the requested medicine."""


class MedicineUnavailableError(Exception):
    """Raised when a medicine cannot be used for dispensing."""


class InsufficientStockError(Exception):
    """Raised when Inventory cannot satisfy the requested quantity."""


class InventoryTransactionNotFoundError(Exception):
    """Raised when a mock Inventory transaction cannot be found."""


class MockInventoryService:
    """Midterm mock implementation of the Inventory integration."""

    def __init__(self):
        self._medicines = [
            {
                "medicine_id": "MED-0001",
                "name": "Paracetamol",
                "generic_name": "Paracetamol",
                "unit": "tablet",
                "quantity_in_stock": 100,
                "reorder_level": 20,
                "status": "ACTIVE",
            },
            {
                "medicine_id": "MED-0002",
                "name": "Ibuprofen",
                "generic_name": "Ibuprofen",
                "unit": "tablet",
                "quantity_in_stock": 15,
                "reorder_level": 20,
                "status": "ACTIVE",
            },
            {
                "medicine_id": "MED-0003",
                "name": "Cetirizine",
                "generic_name": "Cetirizine",
                "unit": "tablet",
                "quantity_in_stock": 0,
                "reorder_level": 10,
                "status": "ACTIVE",
            },
        ]

        self._transactions = {}
        self._next_transaction_number = 1

    @staticmethod
    def _serialize_medicine(medicine):
        result = deepcopy(medicine)
        result["is_low_stock"] = (
            result["quantity_in_stock"] <= result["reorder_level"]
        )
        return result

    def list_medicines(
        self,
        search=None,
        low_stock=None,
        status=None,
        ordering=None,
    ):
        medicines = [
            self._serialize_medicine(medicine)
            for medicine in self._medicines
        ]

        if search:
            term = str(search).strip().lower()
            medicines = [
                medicine
                for medicine in medicines
                if term in medicine["medicine_id"].lower()
                or term in medicine["name"].lower()
                or term in medicine["generic_name"].lower()
            ]

        if low_stock is not None:
            medicines = [
                medicine
                for medicine in medicines
                if medicine["is_low_stock"] == low_stock
            ]

        if status:
            normalized_status = str(status).strip().upper()
            medicines = [
                medicine
                for medicine in medicines
                if medicine["status"] == normalized_status
            ]

        if ordering:
            descending = ordering.startswith("-")
            field = ordering[1:] if descending else ordering

            ordering_fields = {
                "medicine_id",
                "name",
                "generic_name",
                "unit",
                "quantity_in_stock",
                "reorder_level",
                "is_low_stock",
                "status",
            }

            if field in ordering_fields:
                medicines = sorted(
                    medicines,
                    key=lambda medicine: medicine[field],
                    reverse=descending,
                )

        return medicines

    def get_medicine(self, medicine_id):
        medicine_id = str(medicine_id).strip()

        for medicine in self._medicines:
            if medicine["medicine_id"] == medicine_id:
                return self._serialize_medicine(medicine)

        raise MedicineNotFoundError(
            f"Medicine '{medicine_id}' was not found in Inventory."
        )

    def check_stock(self, medicine_id, quantity):
        if quantity < 1:
            raise ValueError("quantity must be greater than or equal to 1.")

        medicine = self.get_medicine(medicine_id)

        return medicine["quantity_in_stock"] >= quantity

    def deduct_stock(self, medicine_id, quantity):
        if quantity < 1:
            raise ValueError("quantity must be greater than or equal to 1.")

        medicine_id = str(medicine_id).strip()

        for medicine in self._medicines:
            if medicine["medicine_id"] != medicine_id:
                continue

            if medicine["status"] != "ACTIVE":
                raise MedicineUnavailableError(
                    f"Medicine '{medicine_id}' is not active."
                )

            if medicine["quantity_in_stock"] < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for medicine '{medicine_id}'."
                )

            medicine["quantity_in_stock"] -= quantity

            transaction_id = (
                f"INV-TX-{self._next_transaction_number:04d}"
            )
            self._next_transaction_number += 1

            self._transactions[transaction_id] = {
                "transaction_id": transaction_id,
                "medicine_id": medicine_id,
                "quantity": quantity,
                "type": "DEDUCTION",
                "rolled_back": False,
            }

            return transaction_id

        raise MedicineNotFoundError(
            f"Medicine '{medicine_id}' was not found in Inventory."
        )

    def restore_stock(self, transaction_id):
        transaction = self._transactions.get(transaction_id)

        if transaction is None:
            raise InventoryTransactionNotFoundError(
                f"Inventory transaction '{transaction_id}' was not found."
            )

        if transaction["rolled_back"]:
            raise ValueError(
                f"Inventory transaction '{transaction_id}' "
                "has already been rolled back."
            )

        medicine_id = transaction["medicine_id"]

        for medicine in self._medicines:
            if medicine["medicine_id"] == medicine_id:
                medicine["quantity_in_stock"] += transaction["quantity"]
                transaction["rolled_back"] = True

                rollback_transaction_id = (
                    f"INV-TX-{self._next_transaction_number:04d}"
                )
                self._next_transaction_number += 1

                self._transactions[rollback_transaction_id] = {
                    "transaction_id": rollback_transaction_id,
                    "medicine_id": medicine_id,
                    "quantity": transaction["quantity"],
                    "type": "RESTORE",
                    "source_transaction_id": transaction_id,
                    "rolled_back": False,
                }

                return rollback_transaction_id

        raise MedicineNotFoundError(
            f"Medicine '{medicine_id}' was not found in Inventory."
        )


inventory_service = MockInventoryService()