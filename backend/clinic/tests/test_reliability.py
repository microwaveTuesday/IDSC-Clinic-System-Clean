from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from rest_framework.test import APIClient
from clinic.models import AuditEvent, OperationReceipt
from clinic.services.inventory import inventory_service
from clinic.services.clinic import clinic_service


class ReliabilityTests(TestCase):
    def setUp(self):
        from copy import deepcopy

        self.inventory_state = deepcopy(inventory_service.__dict__)
        self.user = get_user_model().objects.create_user(
            username="safe_staff", password="WinterGarden!49183"
        )
        self.user.groups.add(Group.objects.get(name="CLINIC_STAFF"))
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        clinic_service.clear_mock_data()

    def tearDown(self):
        inventory_service.__dict__.clear()
        inventory_service.__dict__.update(self.inventory_state)

    def test_idempotent_dispense_deducts_once_and_payload_conflicts(self):
        path = "/api/v1/medicine-dispensations/"
        data = {
            "student_id": "2026-0001",
            "medicine_id": "MED-0001",
            "quantity": 1,
            "reason": "test",
        }
        stock = inventory_service.list_medicines()[0]["quantity_in_stock"]
        first = self.client.post(
            path, data, format="json", HTTP_IDEMPOTENCY_KEY="receipt-one"
        )
        self.assertEqual(first.status_code, 201, first.data)
        again = self.client.post(
            path, data, format="json", HTTP_IDEMPOTENCY_KEY="receipt-one"
        )
        self.assertEqual(again.data, first.data)
        self.assertEqual(again["Idempotency-Replayed"], "true")
        self.assertEqual(
            inventory_service.list_medicines()[0]["quantity_in_stock"], stock - 1
        )
        data["quantity"] = 2
        self.assertEqual(
            self.client.post(
                path, data, format="json", HTTP_IDEMPOTENCY_KEY="receipt-one"
            ).status_code,
            409,
        )
        self.assertEqual(OperationReceipt.objects.count(), 1)
        clinic_service.rollback_dispensation(first.data["dispensation_id"])

    def test_duplicate_rollback_returns_receipt_and_stock_once(self):
        data = {
            "student_id": "2026-0001",
            "medicine_id": "MED-0001",
            "quantity": 1,
            "reason": "test",
        }
        row = self.client.post(
            "/api/v1/medicine-dispensations/", data, format="json"
        ).data
        path = f"/api/v1/medicine-dispensations/{row['dispensation_id']}/rollback/"
        first = self.client.post(
            path, {}, format="json", HTTP_IDEMPOTENCY_KEY="rollback-one"
        )
        again = self.client.post(
            path, {}, format="json", HTTP_IDEMPOTENCY_KEY="rollback-one"
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data, again.data)

    def test_audit_contains_no_password_or_medical_body(self):
        self.client.post(
            "/api/auth/password/change/",
            {"current_password": "wrong", "new_password": "secret"},
            format="json",
        )
        event = AuditEvent.objects.latest("pk")
        self.assertNotIn("secret", str(event.__dict__))
        self.assertEqual(event.actor_id, str(self.user.pk))

    def test_medical_responses_are_not_cached(self):
        self.assertEqual(
            self.client.get("/api/v1/health-records/")["Cache-Control"], "no-store"
        )

    def test_weak_staff_password_is_rejected(self):
        self.user.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        for value in ["x", "password", "123456789"]:
            result = self.client.post(
                "/api/v1/users/",
                {"username": "new_staff", "password": value},
                format="json",
            )
            self.assertEqual(result.status_code, 400)

    @override_settings(LOGIN_THROTTLE_ENABLED=True)
    def test_login_rate_limit(self):
        cache.clear()
        self.client.force_authenticate(None)
        statuses = [
            self.client.post(
                "/api/auth/login/",
                {"username": "none", "password": "wrong"},
                format="json",
            ).status_code
            for _ in range(11)
        ]
        self.assertEqual(statuses[-1], 429)
        cache.clear()

    def test_failed_compensation_records_private_reconciliation_incident(self):
        from unittest.mock import patch
        from clinic.models import IntegrationIncident

        with patch.object(
            clinic_service.repository,
            "create_dispensation",
            side_effect=RuntimeError("persistence"),
        ), patch.object(
            inventory_service, "restore_stock", side_effect=RuntimeError("unavailable")
        ):
            response = self.client.post(
                "/api/v1/medicine-dispensations/",
                {
                    "student_id": "2026-0001",
                    "medicine_id": "MED-0001",
                    "quantity": 1,
                    "reason": "test",
                },
                format="json",
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            IntegrationIncident.objects.get().operation, "COMPENSATION_FAILED"
        )
        self.assertNotIn("transaction_id", response.data)

    def test_idempotency_is_scoped_to_actor(self):
        data = {"student_id": "2026-0001", "blood_type": "O+"}
        self.client.post(
            "/api/v1/health-records/",
            data,
            format="json",
            HTTP_IDEMPOTENCY_KEY="shared-key",
        )
        other = get_user_model().objects.create_user(username="other")
        self.client.force_authenticate(other)
        self.assertEqual(
            self.client.post(
                "/api/v1/health-records/",
                data,
                format="json",
                HTTP_IDEMPOTENCY_KEY="shared-key",
            ).status_code,
            403,
        )

    def test_invalid_version_header_returns_validation_error(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {"student_id": "2026-0001"},
            format="json",
            HTTP_X_RECORD_VERSION="invalid",
        )
        self.assertEqual(response.status_code, 400)

    def test_idempotent_delete_preserves_empty_response(self):
        self.user.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        row = clinic_service.create_health_record({"student_id": "2026-0001"})
        path = f"/api/v1/health-records/{row['health_record_id']}/"
        first = self.client.delete(path, HTTP_IDEMPOTENCY_KEY="delete-one")
        again = self.client.delete(path, HTTP_IDEMPOTENCY_KEY="delete-one")
        self.assertEqual(first.status_code, 204, first.data)
        self.assertEqual(again.status_code, 204)
        self.assertIsNone(again.data)
