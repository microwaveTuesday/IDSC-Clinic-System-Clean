"""Negative security and durable-provider API regression using synthetic data."""

import hashlib
import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from clinic.models import OperationReceipt, IntegrationIncident
from clinic.services.clinic import clinic_service
from clinic.data.persistent import PersistentClinicRepository
from clinic.tests.test_durable_inventory import Provider


class VerificationSecurityTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.provider = Provider(Path(self.temp.name) / "inventory.sqlite3")
        self.user = get_user_model().objects.create_superuser(
            username="synthetic_owner", password="SyntheticGarden!49183"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        for target in (
            "clinic.services.inventory.inventory_service",
            "clinic.services.clinic.inventory_service",
        ):
            p = patch(target, self.provider)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(clinic_service, "repository", PersistentClinicRepository())
        p.start()
        self.addCleanup(p.stop)
        self.path = "/api/v1/medicine-dispensations/"
        self.data = {
            "student_id": "2026-0001",
            "medicine_id": "MED-0001",
            "quantity": 1,
            "reason": "synthetic",
        }

    def send(self, key="synthetic-key"):
        return self.client.post(
            self.path,
            self.data,
            format="json",
            **({"HTTP_IDEMPOTENCY_KEY": key} if key else {}),
        )

    def test_durable_api_success_replay_and_rollback_after_provider_restart(self):
        first = self.send()
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(self.send().data, first.data)
        fresh = Provider(self.provider.path)
        with patch("clinic.services.clinic.inventory_service", fresh):
            result = clinic_service.rollback_dispensation(first.data["dispensation_id"])
        self.assertEqual(result["status"], "ROLLED_BACK")
        self.assertEqual(fresh.get_medicine("MED-0001")["quantity_in_stock"], 100)

    def test_uncertain_request_returns_503_and_records_incident_without_deduction(self):
        scope = hashlib.sha256(f"{self.user.pk}:POST:{self.path}".encode()).hexdigest()
        body = hashlib.sha256(
            json.dumps(self.data, sort_keys=True).encode()
        ).hexdigest()
        self.provider.claim_request(scope, "synthetic-key", body)
        self.assertEqual(self.send().status_code, 503)
        self.assertEqual(self.send().status_code, 503)
        self.assertEqual(IntegrationIncident.objects.count(), 1)
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 100
        )

    def test_durable_api_requires_key(self):
        self.assertEqual(self.send(None).status_code, 400)
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 100
        )

    def test_expired_replay_cannot_reexecute_or_expose_medical_body(self):
        self.assertEqual(self.send().status_code, 201)
        OperationReceipt.objects.update(created_at=timezone.now() - timedelta(days=2))
        response = self.send()
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("synthetic", str(response.data))
        self.assertEqual(
            self.provider.get_medicine("MED-0001")["quantity_in_stock"], 99
        )

    def test_roleless_actor_cannot_read_or_delete_any_clinical_resource(self):
        user = get_user_model().objects.create_user(username="roleless")
        self.client.force_authenticate(user)
        for resource in (
            "health-records",
            "consultations",
            "health-statuses",
            "medicine-dispensations",
        ):
            url = f"/api/v1/{resource}/"
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.delete(url + "1/").status_code, 403)

    def test_login_rejects_structured_or_oversized_credentials(self):
        self.client.force_authenticate(None)
        for data in (
            {"username": {"injection": "x"}, "password": "x"},
            {"username": "x", "password": ["x"]},
            {"username": "x", "password": "x" * 1025},
        ):
            self.assertEqual(
                self.client.post("/api/auth/login/", data, format="json").status_code,
                400,
            )
