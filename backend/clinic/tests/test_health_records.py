from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from clinic.models import HealthRecord


User = get_user_model()

CLINIC_STAFF = "CLINIC_STAFF"
PASSWORD = "TemporaryTest123!"

ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"
INACTIVE_STUDENT = "2026-0003"
MISSING_STUDENT = "9999-9999"


class HealthRecordContractTests(APITestCase):
    """Permanent regression tests for Clinic-owned health records."""

    @classmethod
    def setUpTestData(cls):
        group, _ = Group.objects.get_or_create(
            name=CLINIC_STAFF
        )

        cls.user = User.objects.create_user(
            username="permanent_health_record_staff",
            password=PASSWORD,
        )
        cls.user.groups.add(group)

    def setUp(self):
        self.client.force_authenticate(
            user=self.user
        )

    def create_record(
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
            "height_cm": "170.50",
            "weight_kg": "65.20",
        }
        data.update(overrides)

        return HealthRecord.objects.create(
            **data
        )

    def assert_problem(
        self,
        response,
        expected_status,
    ):
        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertTrue(
            response.get(
                "Content-Type",
                "",
            ).startswith(
                "application/problem+json"
            )
        )

        body = response.json()

        for field in (
            "type",
            "title",
            "status",
            "detail",
            "instance",
            "code",
        ):
            self.assertIn(
                field,
                body,
            )

        self.assertEqual(
            body["status"],
            expected_status,
        )

        return body

    def test_list_returns_canonical_paginated_envelope(self):
        self.create_record()

        response = self.client.get(
            "/api/v1/health-records/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            set(body),
            {
                "count",
                "page",
                "page_size",
                "total_pages",
                "results",
            },
        )
        self.assertEqual(
            body["count"],
            1,
        )
        self.assertEqual(
            body["page"],
            1,
        )
        self.assertEqual(
            body["page_size"],
            20,
        )
        self.assertEqual(
            body["total_pages"],
            1,
        )
        self.assertEqual(
            len(body["results"]),
            1,
        )

    def test_list_filters_by_student_id(self):
        first = self.create_record(
            student_id=ACTIVE_STUDENT
        )
        self.create_record(
            student_id=SECOND_ACTIVE_STUDENT
        )

        response = self.client.get(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            len(results),
            1,
        )
        self.assertEqual(
            results[0]["health_record_id"],
            first.health_record_id,
        )

    def test_list_filters_by_blood_type_case_insensitively(self):
        self.create_record(
            blood_type="O+"
        )
        self.create_record(
            student_id=SECOND_ACTIVE_STUDENT,
            blood_type="A+",
        )

        response = self.client.get(
            "/api/v1/health-records/",
            {
                "blood_type": "o+",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            len(results),
            1,
        )
        self.assertEqual(
            results[0]["blood_type"],
            "O+",
        )

    def test_list_searches_supported_text_fields(self):
        record = self.create_record(
            allergies="Peanut allergy"
        )
        self.create_record(
            student_id=SECOND_ACTIVE_STUDENT,
            allergies="None",
        )

        response = self.client.get(
            "/api/v1/health-records/",
            {
                "search": "peanut",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.json()["results"]

        self.assertEqual(
            len(results),
            1,
        )
        self.assertEqual(
            results[0]["health_record_id"],
            record.health_record_id,
        )

    def test_list_supports_documented_ordering(self):
        first = self.create_record(
            student_id=SECOND_ACTIVE_STUDENT
        )
        second = self.create_record(
            student_id=ACTIVE_STUDENT
        )

        response = self.client.get(
            "/api/v1/health-records/",
            {
                "ordering": "student_id",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        ids = [
            item["health_record_id"]
            for item
            in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [
                second.health_record_id,
                first.health_record_id,
            ],
        )

    def test_invalid_page_returns_canonical_400(self):
        self.create_record()

        response = self.client.get(
            "/api/v1/health-records/",
            {
                "page": 999,
            },
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "errors",
            body,
        )
        self.assertIn(
            "page",
            body["errors"],
        )

    def test_create_accepts_active_registrar_student(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "blood_type": "O+",
                "allergies": "",
                "medical_history": "",
                "current_medications": "",
                "height_cm": "170.50",
                "weight_kg": "65.20",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        body = response.json()

        self.assertEqual(
            body["student_id"],
            ACTIVE_STUDENT,
        )
        self.assertEqual(
            body["blood_type"],
            "O+",
        )
        self.assertEqual(
            HealthRecord.objects.count(),
            1,
        )

    def test_create_rejects_missing_registrar_student_with_404(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    MISSING_STUDENT,
            },
            format="json",
        )

        self.assert_problem(
            response,
            404,
        )

        self.assertEqual(
            HealthRecord.objects.count(),
            0,
        )

    def test_create_rejects_inactive_registrar_student_with_422(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    INACTIVE_STUDENT,
            },
            format="json",
        )

        self.assert_problem(
            response,
            422,
        )

        self.assertEqual(
            HealthRecord.objects.count(),
            0,
        )

    def test_create_rejects_invalid_blood_type(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "blood_type":
                    "INVALID",
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "errors",
            body,
        )
        self.assertIn(
            "blood_type",
            body["errors"],
        )

    def test_create_rejects_nonpositive_height(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "height_cm": 0,
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "height_cm",
            body["errors"],
        )

    def test_create_rejects_height_above_300(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "height_cm": 300.01,
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "height_cm",
            body["errors"],
        )

    def test_create_rejects_nonpositive_weight(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "weight_kg": 0,
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "weight_kg",
            body["errors"],
        )

    def test_create_rejects_weight_above_500(self):
        response = self.client.post(
            "/api/v1/health-records/",
            {
                "student_id":
                    ACTIVE_STUDENT,
                "weight_kg": 500.01,
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "weight_kg",
            body["errors"],
        )

    def test_retrieve_existing_record(self):
        record = self.create_record()

        response = self.client.get(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()[
                "health_record_id"
            ],
            record.health_record_id,
        )

    def test_retrieve_missing_record_returns_404(self):
        response = self.client.get(
            "/api/v1/health-records/999999/"
        )

        self.assert_problem(
            response,
            404,
        )

    def test_put_updates_record_and_validates_student(self):
        record = self.create_record()

        response = self.client.put(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            ),
            {
                "student_id":
                    SECOND_ACTIVE_STUDENT,
                "blood_type": "A+",
                "allergies": "None",
                "medical_history": "Updated",
                "current_medications":
                    "Vitamin C",
                "height_cm": "171.00",
                "weight_kg": "66.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        record.refresh_from_db()

        self.assertEqual(
            record.student_id,
            SECOND_ACTIVE_STUDENT,
        )
        self.assertEqual(
            record.blood_type,
            "A+",
        )
        self.assertEqual(
            record.medical_history,
            "Updated",
        )

    def test_put_rejects_inactive_student(self):
        record = self.create_record()

        response = self.client.put(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            ),
            {
                "student_id":
                    INACTIVE_STUDENT,
            },
            format="json",
        )

        self.assert_problem(
            response,
            422,
        )

        record.refresh_from_db()

        self.assertEqual(
            record.student_id,
            ACTIVE_STUDENT,
        )

    def test_patch_updates_selected_field(self):
        record = self.create_record(
            medical_history="Original"
        )

        response = self.client.patch(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            ),
            {
                "medical_history":
                    "Updated history",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        record.refresh_from_db()

        self.assertEqual(
            record.medical_history,
            "Updated history",
        )
        self.assertEqual(
            record.student_id,
            ACTIVE_STUDENT,
        )

    def test_patch_revalidates_student_when_student_id_changes(self):
        record = self.create_record()

        response = self.client.patch(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            ),
            {
                "student_id":
                    MISSING_STUDENT,
            },
            format="json",
        )

        self.assert_problem(
            response,
            404,
        )

        record.refresh_from_db()

        self.assertEqual(
            record.student_id,
            ACTIVE_STUDENT,
        )

    def test_delete_removes_record(self):
        record = self.create_record()

        response = self.client.delete(
            (
                "/api/v1/health-records/"
                f"{record.health_record_id}/"
            )
        )

        self.assertEqual(
            response.status_code,
            204,
        )
        self.assertFalse(
            HealthRecord.objects.filter(
                health_record_id=(
                    record.health_record_id
                )
            ).exists()
        )

    def test_delete_missing_record_returns_404(self):
        response = self.client.delete(
            "/api/v1/health-records/999999/"
        )

        self.assert_problem(
            response,
            404,
        )
