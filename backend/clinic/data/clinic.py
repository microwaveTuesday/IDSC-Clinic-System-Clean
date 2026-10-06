"""
In-memory data repository for Clinic-owned midterm resources.

Midterm rule:
    Clinic business endpoints use mock/in-memory data and do not require
    persistent Clinic domain tables.

Finals:
    Django models and migrations remain in the repository so a database-backed
    repository can replace this implementation without changing the API layer.

Domain ownership:
    Clinic owns:
    - HealthRecord
    - Consultation
    - HealthStatus
    - MedicineDispensation

    Registrar owns student identity/profile data.
    Inventory owns medicine catalog/stock and inventory transactions.
"""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal


def _utc(year, month, day, hour=0, minute=0):
    return datetime(
        year,
        month,
        day,
        hour,
        minute,
        tzinfo=timezone.utc,
    )


HEALTH_RECORD_SEED = [
    {
        "health_record_id": 1,
        "student_id": "2026-0001",
        "blood_type": "O+",
        "allergies": "Penicillin",
        "medical_history": "",
        "current_medications": "",
        "height_cm": Decimal("170.00"),
        "weight_kg": Decimal("65.00"),
        "created_at": _utc(2026, 9, 1, 8, 0),
        "updated_at": _utc(2026, 9, 1, 8, 0),
    },
    {
        "health_record_id": 2,
        "student_id": "2026-0002",
        "blood_type": "A+",
        "allergies": "",
        "medical_history": "Asthma",
        "current_medications": "Salbutamol as needed",
        "height_cm": Decimal("162.50"),
        "weight_kg": Decimal("54.00"),
        "created_at": _utc(2026, 9, 2, 9, 30),
        "updated_at": _utc(2026, 9, 2, 9, 30),
    },
]


CONSULTATION_SEED = [
    {
        "consultation_id": 1,
        "student_id": "2026-0001",
        "chief_complaint": "Headache",
        "assessment": "Tension headache",
        "treatment": "Rest and hydration",
        "notes": "",
        "consulted_at": _utc(2026, 9, 5, 10, 0),
        "created_at": _utc(2026, 9, 5, 10, 0),
        "updated_at": _utc(2026, 9, 5, 10, 0),
    },
    {
        "consultation_id": 2,
        "student_id": "2026-0002",
        "chief_complaint": "Shortness of breath",
        "assessment": "Mild asthma symptoms",
        "treatment": "Observed and advised inhaler use",
        "notes": "",
        "consulted_at": _utc(2026, 9, 6, 14, 15),
        "created_at": _utc(2026, 9, 6, 14, 15),
        "updated_at": _utc(2026, 9, 6, 14, 15),
    },
]


HEALTH_STATUS_SEED = [
    {
        "status_id": 1,
        "student_id": "2026-0001",
        "status": "CLEARED",
        "remarks": "Fit for regular school activities.",
        "effective_at": _utc(2026, 9, 5, 10, 30),
        "created_at": _utc(2026, 9, 5, 10, 30),
        "updated_at": _utc(2026, 9, 5, 10, 30),
    },
    {
        "status_id": 2,
        "student_id": "2026-0002",
        "status": "UNDER_OBSERVATION",
        "remarks": "Monitor respiratory symptoms.",
        "effective_at": _utc(2026, 9, 6, 14, 30),
        "created_at": _utc(2026, 9, 6, 14, 30),
        "updated_at": _utc(2026, 9, 6, 14, 30),
    },
]


DISPENSATION_SEED = [
    {
        "dispensation_id": 1,
        "student_id": "2026-0001",
        "medicine_id": "MED-0001",
        "quantity": 1,
        "reason": "Headache",
        "status": "COMPLETED",
        "inventory_transaction_id": "INV-TX-0001",
        "rollback_transaction_id": None,
        "dispensed_at": _utc(2026, 9, 5, 10, 15),
        "rolled_back_at": None,
        "created_at": _utc(2026, 9, 5, 10, 15),
    },
]


class MockClinicRepository:
    """
    Mutable in-memory repository for Clinic-owned resources.

    Every returned record is deep-copied so callers cannot mutate repository
    state accidentally.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._health_records = {
            row["health_record_id"]: deepcopy(row)
            for row in HEALTH_RECORD_SEED
        }

        self._consultations = {
            row["consultation_id"]: deepcopy(row)
            for row in CONSULTATION_SEED
        }

        self._health_statuses = {
            row["status_id"]: deepcopy(row)
            for row in HEALTH_STATUS_SEED
        }

        self._dispensations = {
            row["dispensation_id"]: deepcopy(row)
            for row in DISPENSATION_SEED
        }

        self._next_health_record_id = (
            max(self._health_records, default=0) + 1
        )

        self._next_consultation_id = (
            max(self._consultations, default=0) + 1
        )

        self._next_status_id = (
            max(self._health_statuses, default=0) + 1
        )

        self._next_dispensation_id = (
            max(self._dispensations, default=0) + 1
        )

    def clear(self):
        """
        Remove all Clinic-owned mock records.

        Runtime reset() restores realistic demonstration seed data.
        Tests use clear() so every contract test can start from a
        deterministic empty Clinic domain store.
        """

        self._health_records = {}
        self._consultations = {}
        self._health_statuses = {}
        self._dispensations = {}

        self._next_health_record_id = 1
        self._next_consultation_id = 1
        self._next_status_id = 1
        self._next_dispensation_id = 1

    @staticmethod
    def _copy(value):
        return deepcopy(value)

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Health records
    # ------------------------------------------------------------------

    def list_health_records(self):
        return self._copy(list(self._health_records.values()))

    def get_health_record(self, health_record_id):
        record = self._health_records.get(int(health_record_id))
        return self._copy(record) if record is not None else None

    def create_health_record(self, values):
        now = self._now()

        record = {
            "health_record_id": self._next_health_record_id,
            "student_id": values["student_id"],
            "blood_type": values.get("blood_type", ""),
            "allergies": values.get("allergies", ""),
            "medical_history": values.get("medical_history", ""),
            "current_medications": values.get(
                "current_medications",
                "",
            ),
            "height_cm": values.get("height_cm"),
            "weight_kg": values.get("weight_kg"),
            "created_at": now,
            "updated_at": now,
        }

        self._health_records[
            self._next_health_record_id
        ] = record

        self._next_health_record_id += 1

        return self._copy(record)

    def update_health_record(self, health_record_id, values):
        key = int(health_record_id)

        if key not in self._health_records:
            return None

        self._health_records[key].update(values)
        self._health_records[key]["updated_at"] = self._now()

        return self._copy(self._health_records[key])

    def delete_health_record(self, health_record_id):
        record = self._health_records.pop(
            int(health_record_id),
            None,
        )

        return self._copy(record) if record is not None else None

    # ------------------------------------------------------------------
    # Consultations
    # ------------------------------------------------------------------

    def list_consultations(self):
        return self._copy(list(self._consultations.values()))

    def get_consultation(self, consultation_id):
        record = self._consultations.get(int(consultation_id))
        return self._copy(record) if record is not None else None

    def create_consultation(self, values):
        now = self._now()

        record = {
            "consultation_id": self._next_consultation_id,
            "student_id": values["student_id"],
            "chief_complaint": values["chief_complaint"],
            "assessment": values.get("assessment", ""),
            "treatment": values.get("treatment", ""),
            "notes": values.get("notes", ""),
            "consulted_at": now,
            "created_at": now,
            "updated_at": now,
        }

        self._consultations[
            self._next_consultation_id
        ] = record

        self._next_consultation_id += 1

        return self._copy(record)

    def update_consultation(self, consultation_id, values):
        key = int(consultation_id)

        if key not in self._consultations:
            return None

        self._consultations[key].update(values)
        self._consultations[key]["updated_at"] = self._now()

        return self._copy(self._consultations[key])

    def delete_consultation(self, consultation_id):
        record = self._consultations.pop(
            int(consultation_id),
            None,
        )

        return self._copy(record) if record is not None else None

    # ------------------------------------------------------------------
    # Health statuses
    # ------------------------------------------------------------------

    def list_health_statuses(self):
        return self._copy(list(self._health_statuses.values()))

    def get_health_status(self, status_id):
        record = self._health_statuses.get(int(status_id))
        return self._copy(record) if record is not None else None

    def create_health_status(self, values):
        now = self._now()

        record = {
            "status_id": self._next_status_id,
            "student_id": values["student_id"],
            "status": values["status"],
            "remarks": values.get("remarks", ""),
            "effective_at": now,
            "created_at": now,
            "updated_at": now,
        }

        self._health_statuses[
            self._next_status_id
        ] = record

        self._next_status_id += 1

        return self._copy(record)

    def update_health_status(self, status_id, values):
        key = int(status_id)

        if key not in self._health_statuses:
            return None

        self._health_statuses[key].update(values)
        self._health_statuses[key]["updated_at"] = self._now()

        return self._copy(self._health_statuses[key])

    def delete_health_status(self, status_id):
        record = self._health_statuses.pop(
            int(status_id),
            None,
        )

        return self._copy(record) if record is not None else None

    def get_latest_health_status_for_student(self, student_id):
        records = [
            row
            for row in self._health_statuses.values()
            if row["student_id"] == student_id
        ]

        if not records:
            return None

        latest = max(
            records,
            key=lambda row: (
                row["effective_at"],
                row["status_id"],
            ),
        )

        return self._copy(latest)

    # ------------------------------------------------------------------
    # Medicine dispensations
    # ------------------------------------------------------------------

    def list_dispensations(self):
        return self._copy(list(self._dispensations.values()))

    def get_dispensation(self, dispensation_id):
        record = self._dispensations.get(int(dispensation_id))
        return self._copy(record) if record is not None else None

    def create_dispensation(
        self,
        values,
        inventory_transaction_id,
    ):
        now = self._now()

        record = {
            "dispensation_id": self._next_dispensation_id,
            "student_id": values["student_id"],
            "medicine_id": values["medicine_id"],
            "quantity": values["quantity"],
            "reason": values.get("reason", ""),
            "status": "COMPLETED",
            "inventory_transaction_id": inventory_transaction_id,
            "rollback_transaction_id": None,
            "dispensed_at": now,
            "rolled_back_at": None,
            "created_at": now,
        }

        self._dispensations[
            self._next_dispensation_id
        ] = record

        self._next_dispensation_id += 1

        return self._copy(record)

    def rollback_dispensation(
        self,
        dispensation_id,
        rollback_transaction_id,
    ):
        key = int(dispensation_id)

        if key not in self._dispensations:
            return None

        self._dispensations[key]["status"] = "ROLLED_BACK"
        self._dispensations[key][
            "rollback_transaction_id"
        ] = rollback_transaction_id
        self._dispensations[key][
            "rolled_back_at"
        ] = self._now()

        return self._copy(self._dispensations[key])


mock_clinic_repository = MockClinicRepository()
