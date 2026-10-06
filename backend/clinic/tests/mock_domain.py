"""
Reusable Clinic mock-domain fixtures for contract tests.

Django authentication/groups/sessions continue to use Django's SQLite
test database.

Clinic business/domain fixtures use ClinicService -> MockClinicRepository
and never create HealthRecord, Consultation, HealthStatus, or
MedicineDispensation ORM rows.
"""

from copy import deepcopy


ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"


class MockDomainRecord:
    """
    Small test proxy that preserves the convenient attribute syntax used
    by the former ORM-based contract tests.

    Example:
        record.health_record_id
        record.student_id
        record.refresh_from_db()
    """

    def __init__(
        self,
        getter,
        id_field,
        record,
    ):
        self._getter = getter
        self._id_field = id_field
        self._data = deepcopy(record)

    def refresh_from_db(self):
        record_id = self._data[self._id_field]
        latest = self._getter(record_id)

        if latest is None:
            raise LookupError(
                f"Mock record {record_id!r} no longer exists."
            )

        self._data = deepcopy(latest)
        return self

    def as_dict(self):
        return deepcopy(self._data)

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


class MockDomainTestMixin:
    """
    Helpers for Clinic contract tests.

    Call reset_mock_domain() from each test class setUp().
    """

    def reset_mock_domain(self):
        from clinic.services.clinic import clinic_service

        clinic_service.clear_mock_data()

    @property
    def clinic_repository(self):
        from clinic.services.clinic import clinic_service

        return clinic_service.repository

    # --------------------------------------------------------
    # Health records
    # --------------------------------------------------------

    def create_mock_health_record(
        self,
        student_id=ACTIVE_STUDENT,
        **overrides,
    ):
        data = {
            "student_id": student_id,
            "blood_type": "O+",
            "allergies": "Penicillin",
            "medical_history": "History of asthma",
            "current_medications": "None",
            "height_cm": None,
            "weight_kg": None,
        }

        data.update(overrides)

        record = (
            self.clinic_repository
            .create_health_record(data)
        )

        return MockDomainRecord(
            self.clinic_repository.get_health_record,
            "health_record_id",
            record,
        )

    def health_record_count(self):
        return len(
            self.clinic_repository.list_health_records()
        )

    def health_record_exists(
        self,
        health_record_id,
    ):
        return (
            self.clinic_repository.get_health_record(
                health_record_id
            )
            is not None
        )

    # --------------------------------------------------------
    # Consultations
    # --------------------------------------------------------

    def create_mock_consultation(
        self,
        student_id=ACTIVE_STUDENT,
        **overrides,
    ):
        data = {
            "student_id": student_id,
            "chief_complaint": "Headache",
            "assessment": "Tension headache",
            "treatment": "Rest and hydration",
            "notes": "Return if symptoms persist",
        }

        data.update(overrides)

        record = (
            self.clinic_repository
            .create_consultation(data)
        )

        return MockDomainRecord(
            self.clinic_repository.get_consultation,
            "consultation_id",
            record,
        )

    def consultation_count(self):
        return len(
            self.clinic_repository.list_consultations()
        )

    def set_consulted_at(
        self,
        consultation_id,
        value,
    ):
        self.clinic_repository.update_consultation(
            consultation_id,
            {
                "consulted_at": value,
            },
        )

    def consultation_exists(
        self,
        consultation_id,
    ):
        return (
            self.clinic_repository.get_consultation(
                consultation_id
            )
            is not None
        )

    # --------------------------------------------------------
    # Health statuses
    # --------------------------------------------------------

    def create_mock_health_status(
        self,
        student_id=ACTIVE_STUDENT,
        status="CLEARED",
        **overrides,
    ):
        data = {
            "student_id": student_id,
            "status": status,
            "remarks": "Cleared for regular activities",
        }

        data.update(overrides)

        record = (
            self.clinic_repository
            .create_health_status(data)
        )

        return MockDomainRecord(
            self.clinic_repository.get_health_status,
            "status_id",
            record,
        )

    def health_status_count(self):
        return len(
            self.clinic_repository.list_health_statuses()
        )

    def set_effective_at(
        self,
        status_id,
        value,
    ):
        self.clinic_repository.update_health_status(
            status_id,
            {
                "effective_at": value,
            },
        )

    def health_status_exists(
        self,
        status_id,
    ):
        return (
            self.clinic_repository.get_health_status(
                status_id
            )
            is not None
        )

    # --------------------------------------------------------
    # Medicine dispensations
    # --------------------------------------------------------

    def dispensation_count(self):
        return len(
            self.clinic_repository.list_dispensations()
        )

    def dispensation_exists(
        self,
        dispensation_id,
    ):
        return (
            self.clinic_repository.get_dispensation(
                dispensation_id
            )
            is not None
        )

    def set_dispensed_at(
        self,
        dispensation_id,
        value,
    ):
        record = (
            self.clinic_repository
            ._dispensations
            .get(int(dispensation_id))
        )

        if record is None:
            raise LookupError(
                f"Dispensation {dispensation_id!r} not found."
            )

        record["dispensed_at"] = value

    # --------------------------------------------------------
    # General assertions
    # --------------------------------------------------------

    def assert_mock_domain_empty(self):
        counts = {
            "health_records":
                self.health_record_count(),
            "consultations":
                self.consultation_count(),
            "health_statuses":
                self.health_status_count(),
            "dispensations":
                self.dispensation_count(),
        }

        if any(counts.values()):
            raise AssertionError(
                f"Clinic mock domain is not empty: {counts}"
            )

        return counts
