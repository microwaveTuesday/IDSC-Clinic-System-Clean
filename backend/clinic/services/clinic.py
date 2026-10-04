"""
Service layer for Clinic-owned domain resources.

Views must use this service instead of talking directly to Django ORM models.

For the midterm, this service is backed by MockClinicRepository.
A database repository can replace it for finals without changing API routes.
"""

from .registrar import (
    StudentNotFoundError,
    StudentUnavailableError,
    registrar_service,
)

from .inventory import (
    InsufficientStockError,
    InventoryTransactionNotFoundError,
    MedicineNotFoundError,
    MedicineUnavailableError,
    inventory_service,
)

from ..data.clinic import mock_clinic_repository


class ClinicResourceNotFoundError(Exception):
    pass


class ClinicDispensationAlreadyRolledBackError(Exception):
    pass


class ClinicDispensationRollbackUnavailableError(Exception):
    pass


class ClinicService:
    def __init__(self, repository=None):
        self.repository = (
            repository or mock_clinic_repository
        )

    def reset_mock_data(self):
        """Restore the normal runtime demonstration seed data."""
        self.repository.reset()

    def clear_mock_data(self):
        """Start with an empty Clinic domain store for isolated tests."""
        self.repository.clear()

    # --------------------------------------------------------------
    # Health records
    # --------------------------------------------------------------

    def list_health_records(
        self,
        student_id="",
        blood_type="",
        search="",
        ordering="",
    ):
        records = self.repository.list_health_records()

        if student_id:
            records = [
                row
                for row in records
                if row["student_id"] == student_id
            ]

        if blood_type:
            target = blood_type.lower()

            records = [
                row
                for row in records
                if str(
                    row.get("blood_type", "")
                ).lower() == target
            ]

        if search:
            needle = search.lower()

            records = [
                row
                for row in records
                if needle in row["student_id"].lower()
                or needle in str(
                    row.get("allergies", "")
                ).lower()
                or needle in str(
                    row.get("medical_history", "")
                ).lower()
                or needle in str(
                    row.get(
                        "current_medications",
                        "",
                    )
                ).lower()
            ]

        allowed_ordering = {
            "health_record_id",
            "student_id",
            "blood_type",
            "created_at",
            "updated_at",
        }

        if ordering:
            descending = ordering.startswith("-")
            field = (
                ordering[1:]
                if descending
                else ordering
            )

            if field in allowed_ordering:
                records.sort(
                    key=lambda row: (
                        row.get(field) is None,
                        row.get(field),
                    ),
                    reverse=descending,
                )

                return records

        return sorted(
            records,
            key=lambda row: (
                row["created_at"],
                row["health_record_id"],
            ),
            reverse=True,
        )

    def get_health_record(self, health_record_id):
        record = self.repository.get_health_record(
            health_record_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health record '{health_record_id}' was not found."
            )

        return record

    def create_health_record(self, values):
        self._validate_student(values["student_id"])

        return self.repository.create_health_record(values)

    def update_health_record(
        self,
        health_record_id,
        values,
    ):
        current = self.get_health_record(
            health_record_id
        )

        student_id = values.get(
            "student_id",
            current["student_id"],
        )

        self._validate_student(student_id)

        record = self.repository.update_health_record(
            health_record_id,
            values,
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health record '{health_record_id}' was not found."
            )

        return record

    def delete_health_record(self, health_record_id):
        record = self.repository.delete_health_record(
            health_record_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health record '{health_record_id}' was not found."
            )

        return record

    # --------------------------------------------------------------
    # Consultations
    # --------------------------------------------------------------

    def list_consultations(
        self,
        student_id="",
        search="",
        date_from=None,
        date_to=None,
        ordering="",
    ):
        records = self.repository.list_consultations()

        if student_id:
            records = [
                row
                for row in records
                if row["student_id"] == student_id
            ]

        if search:
            needle = search.lower()

            records = [
                row
                for row in records
                if needle in str(
                    row.get(
                        "chief_complaint",
                        "",
                    )
                ).lower()
                or needle in str(
                    row.get("assessment", "")
                ).lower()
                or needle in str(
                    row.get("treatment", "")
                ).lower()
                or needle in str(
                    row.get("notes", "")
                ).lower()
            ]

        if date_from:
            records = [
                row
                for row in records
                if row["consulted_at"].date()
                >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["consulted_at"].date()
                <= date_to
            ]

        allowed_ordering = {
            "consultation_id",
            "student_id",
            "consulted_at",
            "created_at",
            "updated_at",
        }

        if ordering:
            descending = ordering.startswith("-")
            field = (
                ordering[1:]
                if descending
                else ordering
            )

            if field in allowed_ordering:
                records.sort(
                    key=lambda row: (
                        row.get(field) is None,
                        row.get(field),
                    ),
                    reverse=descending,
                )

                return records

        return sorted(
            records,
            key=lambda row: (
                row["consulted_at"],
                row["consultation_id"],
            ),
            reverse=True,
        )

    def get_consultation(self, consultation_id):
        record = self.repository.get_consultation(
            consultation_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Consultation '{consultation_id}' was not found."
            )

        return record

    def create_consultation(self, values):
        self._validate_student(values["student_id"])

        return self.repository.create_consultation(values)

    def update_consultation(
        self,
        consultation_id,
        values,
    ):
        current = self.get_consultation(
            consultation_id
        )

        student_id = values.get(
            "student_id",
            current["student_id"],
        )

        self._validate_student(student_id)

        record = self.repository.update_consultation(
            consultation_id,
            values,
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Consultation '{consultation_id}' was not found."
            )

        return record

    def delete_consultation(self, consultation_id):
        record = self.repository.delete_consultation(
            consultation_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Consultation '{consultation_id}' was not found."
            )

        return record

    # --------------------------------------------------------------
    # Health statuses
    # --------------------------------------------------------------

    def list_health_statuses(
        self,
        student_id="",
        status="",
        date_from=None,
        date_to=None,
        ordering="",
    ):
        records = self.repository.list_health_statuses()

        if student_id:
            records = [
                row
                for row in records
                if row["student_id"] == student_id
            ]

        if status:
            records = [
                row
                for row in records
                if row["status"] == status
            ]

        if date_from:
            records = [
                row
                for row in records
                if row["effective_at"].date()
                >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["effective_at"].date()
                <= date_to
            ]

        allowed_ordering = {
            "status_id",
            "student_id",
            "status",
            "effective_at",
            "created_at",
            "updated_at",
        }

        if ordering:
            descending = ordering.startswith("-")
            field = (
                ordering[1:]
                if descending
                else ordering
            )

            if field in allowed_ordering:
                records.sort(
                    key=lambda row: (
                        row.get(field) is None,
                        row.get(field),
                    ),
                    reverse=descending,
                )

                return records

        return sorted(
            records,
            key=lambda row: (
                row["effective_at"],
                row["status_id"],
            ),
            reverse=True,
        )

    def get_health_status(self, status_id):
        record = self.repository.get_health_status(
            status_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health status '{status_id}' was not found."
            )

        return record

    def create_health_status(self, values):
        self._validate_student(values["student_id"])

        return self.repository.create_health_status(values)

    def update_health_status(
        self,
        status_id,
        values,
    ):
        current = self.get_health_status(status_id)

        student_id = values.get(
            "student_id",
            current["student_id"],
        )

        self._validate_student(student_id)

        record = self.repository.update_health_status(
            status_id,
            values,
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health status '{status_id}' was not found."
            )

        return record

    def delete_health_status(self, status_id):
        record = self.repository.delete_health_status(
            status_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Health status '{status_id}' was not found."
            )

        return record

    def latest_health_status_for_student(
        self,
        student_id,
    ):
        registrar_service.get_student(student_id)

        return (
            self.repository
            .get_latest_health_status_for_student(student_id)
        )

    # --------------------------------------------------------------
    # Medicine dispensations
    # --------------------------------------------------------------

    def list_dispensations(
        self,
        student_id="",
        medicine_id="",
        status="",
        search="",
        date_from=None,
        date_to=None,
        ordering="",
    ):
        records = self.repository.list_dispensations()

        if student_id:
            records = [
                row
                for row in records
                if row["student_id"] == student_id
            ]

        if medicine_id:
            records = [
                row
                for row in records
                if row["medicine_id"] == medicine_id
            ]

        if status:
            records = [
                row
                for row in records
                if row["status"] == status
            ]

        if search:
            needle = search.lower()

            records = [
                row
                for row in records
                if needle in row["student_id"].lower()
                or needle in row["medicine_id"].lower()
                or needle in str(
                    row.get("reason", "")
                ).lower()
                or needle in str(
                    row.get(
                        "inventory_transaction_id",
                        "",
                    )
                ).lower()
                or needle in str(
                    row.get(
                        "rollback_transaction_id",
                        "",
                    )
                ).lower()
            ]

        if date_from:
            records = [
                row
                for row in records
                if row["dispensed_at"].date() >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["dispensed_at"].date() <= date_to
            ]

        allowed_ordering = {
            "dispensation_id",
            "student_id",
            "medicine_id",
            "quantity",
            "status",
            "dispensed_at",
            "created_at",
        }

        if ordering:
            descending = ordering.startswith("-")
            field = (
                ordering[1:]
                if descending
                else ordering
            )

            if field in allowed_ordering:
                records.sort(
                    key=lambda row: (
                        row.get(field) is None,
                        row.get(field),
                    ),
                    reverse=descending,
                )

                return records

        return sorted(
            records,
            key=lambda row: (
                row["dispensed_at"],
                row["dispensation_id"],
            ),
            reverse=True,
        )

    def get_dispensation(self, dispensation_id):
        record = self.repository.get_dispensation(
            dispensation_id
        )

        if record is None:
            raise ClinicResourceNotFoundError(
                f"Medicine dispensation "
                f"'{dispensation_id}' was not found."
            )

        return record

    def create_dispensation(self, values):
        """
        Coordinate Registrar validation, Inventory deduction,
        and Clinic mock persistence.

        If Clinic persistence fails after Inventory deduction,
        compensate by restoring Inventory stock.
        """

        self._validate_student(
            values["student_id"]
        )

        inventory_transaction_id = (
            inventory_service.deduct_stock(
                values["medicine_id"],
                values["quantity"],
            )
        )

        try:
            return self.repository.create_dispensation(
                values,
                inventory_transaction_id,
            )
        except Exception:
            try:
                inventory_service.restore_stock(
                    inventory_transaction_id
                )
            except Exception:
                # Preserve the original Clinic persistence
                # failure as the primary exception.
                pass

            raise

    def rollback_dispensation(
        self,
        dispensation_id,
    ):
        """
        Restore Inventory stock, then record the Clinic-owned
        dispensation as rolled back.
        """

        record = self.get_dispensation(
            dispensation_id
        )

        if record["status"] == "ROLLED_BACK":
            raise (
                ClinicDispensationAlreadyRolledBackError(
                    f"Dispensation "
                    f"'{record['dispensation_id']}' "
                    "has already been rolled back."
                )
            )

        inventory_transaction_id = (
            record.get(
                "inventory_transaction_id"
            )
        )

        if not inventory_transaction_id:
            raise (
                ClinicDispensationRollbackUnavailableError(
                    f"Dispensation "
                    f"'{record['dispensation_id']}' "
                    "does not have an Inventory "
                    "transaction to roll back."
                )
            )

        rollback_transaction_id = (
            inventory_service.restore_stock(
                inventory_transaction_id
            )
        )

        try:
            updated = (
                self.repository
                .rollback_dispensation(
                    dispensation_id,
                    rollback_transaction_id,
                )
            )
        except Exception:
            # Inventory has already restored the stock.
            # Surface the Clinic data-layer failure instead of
            # pretending the external action was reverted.
            raise

        if updated is None:
            raise ClinicResourceNotFoundError(
                f"Medicine dispensation "
                f"'{dispensation_id}' was not found."
            )

        return updated

    # --------------------------------------------------------------
    # Reports
    # --------------------------------------------------------------

    def report_consultations(
        self,
        date_from=None,
        date_to=None,
    ):
        records = self.list_consultations()

        if date_from:
            records = [
                row
                for row in records
                if row["consulted_at"].date() >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["consulted_at"].date() <= date_to
            ]

        return records

    def report_health_records(
        self,
        date_from=None,
        date_to=None,
    ):
        records = self.list_health_records()

        if date_from:
            records = [
                row
                for row in records
                if row["created_at"].date() >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["created_at"].date() <= date_to
            ]

        return records

    def report_dispensations(
        self,
        date_from=None,
        date_to=None,
        student_id="",
        medicine_id="",
        status="",
    ):
        records = self.list_dispensations()

        if date_from:
            records = [
                row
                for row in records
                if row["dispensed_at"].date() >= date_from
            ]

        if date_to:
            records = [
                row
                for row in records
                if row["dispensed_at"].date() <= date_to
            ]

        if student_id:
            records = [
                row
                for row in records
                if row["student_id"] == student_id
            ]

        if medicine_id:
            records = [
                row
                for row in records
                if row["medicine_id"] == medicine_id
            ]

        if status:
            records = [
                row
                for row in records
                if row["status"] == status
            ]

        return records

    # --------------------------------------------------------------
    # Dashboard helper
    # --------------------------------------------------------------

    def total_health_records(self):
        return len(
            self.repository.list_health_records()
        )

    def recent_activity(self, limit=10):
        activities = []

        for row in self.repository.list_health_records():
            activities.append(
                {
                    "activity_type": "HEALTH_RECORD",
                    "reference_id": row[
                        "health_record_id"
                    ],
                    "student_id": row["student_id"],
                    "occurred_at": row["created_at"],
                }
            )

        for row in self.repository.list_consultations():
            activities.append(
                {
                    "activity_type": "CONSULTATION",
                    "reference_id": row[
                        "consultation_id"
                    ],
                    "student_id": row["student_id"],
                    "occurred_at": row["consulted_at"],
                }
            )

        for row in self.repository.list_health_statuses():
            activities.append(
                {
                    "activity_type": "HEALTH_STATUS",
                    "reference_id": row["status_id"],
                    "student_id": row["student_id"],
                    "occurred_at": row["effective_at"],
                }
            )

        for row in self.repository.list_dispensations():
            activities.append(
                {
                    "activity_type": "MEDICINE_DISPENSATION",
                    "reference_id": row[
                        "dispensation_id"
                    ],
                    "student_id": row["student_id"],
                    "occurred_at": row["dispensed_at"],
                }
            )

        activities.sort(
            key=lambda row: row["occurred_at"],
            reverse=True,
        )

        return activities[:limit]

    @staticmethod
    def _validate_student(student_id):
        try:
            registrar_service.validate_student_for_clinic(
                student_id
            )
        except (
            StudentNotFoundError,
            StudentUnavailableError,
        ):
            raise


clinic_service = ClinicService()
