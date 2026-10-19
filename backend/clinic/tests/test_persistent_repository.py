from django.test import TestCase
from django.db import IntegrityError, transaction
from clinic.data.persistent import PersistentClinicRepository
from clinic.models import HealthRecord, MedicineDispensation
from clinic.mutations import expected_etag, record_etag
from clinic.exceptions import ConflictError


class PersistentRepositoryTests(TestCase):
    def setUp(self):
        self.repo = PersistentClinicRepository()

    def test_crud_and_new_instance_reads_durable_rows(self):
        for kind, values in [
            ("health_record", {"student_id": "external-1", "blood_type": "O+"}),
            (
                "consultation",
                {"student_id": "external-1", "chief_complaint": "Headache"},
            ),
            ("health_status", {"student_id": "external-1", "status": "CLEARED"}),
        ]:
            row = getattr(self.repo, "create_" + kind)(values)
            model = self.repo.models[kind]
            key = row[model._meta.pk.name]
            other = PersistentClinicRepository()
            self.assertEqual(getattr(other, "get_" + kind)(key), row)
            self.assertIsNotNone(
                getattr(other, "update_" + kind)(key, {"student_id": "external-2"})
            )
            getattr(other, "delete_" + kind)(key)
            self.assertIsNone(getattr(self.repo, "get_" + kind)(key))

    def test_dispensation_rollback_and_history_delete(self):
        row = self.repo.create_dispensation(
            {"student_id": "s", "medicine_id": "m", "quantity": 2}, "external-tx"
        )
        self.assertEqual(
            self.repo.rollback_dispensation(row["dispensation_id"], "external-restore")[
                "status"
            ],
            "ROLLED_BACK",
        )
        self.repo.delete_dispensation(row["dispensation_id"])
        self.assertEqual(MedicineDispensation.objects.count(), 0)

    def test_stale_update_and_delete_conflict(self):
        row = self.repo.create_health_record({"student_id": "s"})
        token = expected_etag.set(record_etag(row))
        try:
            self.repo.update_health_record(
                row["health_record_id"], {"allergies": "updated"}
            )
            with self.assertRaises(ConflictError):
                self.repo.update_health_record(
                    row["health_record_id"], {"allergies": "lost"}
                )
            with self.assertRaises(ConflictError):
                self.repo.delete_health_record(row["health_record_id"])
        finally:
            expected_etag.reset(token)

    def test_quantity_constraint_and_transaction_reference_uniqueness(self):
        data = {
            "student_id": "s",
            "medicine_id": "m",
            "quantity": 1,
            "inventory_transaction_id": "tx",
        }
        MedicineDispensation.objects.create(**data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MedicineDispensation.objects.create(**data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            MedicineDispensation.objects.create(
                student_id="s", medicine_id="m", quantity=0
            )

    def test_latest_status_and_missing_resource(self):
        self.repo.create_health_status({"student_id": "s", "status": "CLEARED"})
        self.assertEqual(
            self.repo.get_latest_health_status_for_student("s")["status"], "CLEARED"
        )
        self.assertIsNone(self.repo.get_health_record(999))

    def test_configured_api_create_update_delete_uses_database(self):
        from unittest.mock import patch
        from rest_framework.test import APIClient
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        from clinic.services.clinic import clinic_service

        user = get_user_model().objects.create_user(username="persistent_api")
        group, _ = Group.objects.get_or_create(name="CLINIC_ADMIN")
        user.groups.add(group)
        client = APIClient()
        client.force_authenticate(user)
        with patch.object(clinic_service, "repository", self.repo):
            created = client.post(
                "/api/v1/health-records/",
                {"student_id": "2026-0001", "blood_type": "O+"},
                format="json",
            )
            self.assertEqual(created.status_code, 201, created.data)
            key = created.data["health_record_id"]
            url = f"/api/v1/health-records/{key}/"
            latest = client.get(url)
            updated = client.patch(
                url,
                {"allergies": "Updated"},
                format="json",
                HTTP_IF_MATCH=latest["ETag"],
            )
            self.assertEqual(updated.status_code, 200, updated.data)
            stale = client.patch(
                url, {"allergies": "Lost"}, format="json", HTTP_IF_MATCH=latest["ETag"]
            )
            self.assertEqual(stale.status_code, 409)
            self.assertEqual(client.delete(url).status_code, 204)
            self.assertEqual(HealthRecord.objects.count(), 0)
