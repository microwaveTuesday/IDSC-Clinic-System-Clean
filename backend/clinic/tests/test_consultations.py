from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APITestCase

from clinic.models import Consultation


User = get_user_model()

CLINIC_STAFF = "CLINIC_STAFF"
PASSWORD = "TemporaryTest123!"

ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"
INACTIVE_STUDENT = "2026-0003"
MISSING_STUDENT = "9999-9999"


class ConsultationContractTests(APITestCase):
    """Permanent regression tests for Clinic consultation records."""

    @classmethod
    def setUpTestData(cls):
        group, _ = Group.objects.get_or_create(
            name=CLINIC_STAFF
        )

        cls.user = User.objects.create_user(
            username="permanent_consultation_staff",
            password=PASSWORD,
        )
        cls.user.groups.add(group)

    def setUp(self):
        self.client.force_authenticate(
            user=self.user
        )

    def create_consultation(
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

        return Consultation.objects.create(
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
            self.assertIn(field, body)

        self.assertEqual(
            body["status"],
            expected_status,
        )

        return body

    def test_list_returns_canonical_paginated_envelope(self):
        self.create_consultation()

        response = self.client.get(
            "/api/v1/consultations/"
        )

        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 20)
        self.assertEqual(body["total_pages"], 1)
        self.assertEqual(len(body["results"]), 1)

    def test_default_ordering_is_latest_consultation_first(self):
        first = self.create_consultation()
        second = self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT
        )

        old_time = timezone.now() - timedelta(days=2)
        new_time = timezone.now()

        Consultation.objects.filter(
            consultation_id=first.consultation_id
        ).update(consulted_at=old_time)

        Consultation.objects.filter(
            consultation_id=second.consultation_id
        ).update(consulted_at=new_time)

        response = self.client.get(
            "/api/v1/consultations/"
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["consultation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [
                second.consultation_id,
                first.consultation_id,
            ],
        )

    def test_list_filters_by_student_id(self):
        first = self.create_consultation()
        self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT
        )

        response = self.client.get(
            "/api/v1/consultations/",
            {"student_id": ACTIVE_STUDENT},
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["consultation_id"],
            first.consultation_id,
        )

    def test_list_searches_supported_text_fields(self):
        target = self.create_consultation(
            chief_complaint="Severe dizziness"
        )
        self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT,
            chief_complaint="Fever",
        )

        response = self.client.get(
            "/api/v1/consultations/",
            {"search": "dizziness"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["consultation_id"],
            target.consultation_id,
        )

    def test_list_supports_documented_ordering(self):
        first = self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT
        )
        second = self.create_consultation(
            student_id=ACTIVE_STUDENT
        )

        response = self.client.get(
            "/api/v1/consultations/",
            {"ordering": "student_id"},
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["consultation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [
                second.consultation_id,
                first.consultation_id,
            ],
        )

    def test_date_from_filter_is_inclusive(self):
        old = self.create_consultation()
        recent = self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT
        )

        now = timezone.now()
        old_time = now - timedelta(days=2)

        Consultation.objects.filter(
            consultation_id=old.consultation_id
        ).update(consulted_at=old_time)

        Consultation.objects.filter(
            consultation_id=recent.consultation_id
        ).update(consulted_at=now)

        response = self.client.get(
            "/api/v1/consultations/",
            {
                "date_from":
                    now.date().isoformat()
            },
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["consultation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [recent.consultation_id],
        )

    def test_date_to_filter_is_inclusive(self):
        old = self.create_consultation()
        recent = self.create_consultation(
            student_id=SECOND_ACTIVE_STUDENT
        )

        now = timezone.now()
        old_time = now - timedelta(days=2)

        Consultation.objects.filter(
            consultation_id=old.consultation_id
        ).update(consulted_at=old_time)

        Consultation.objects.filter(
            consultation_id=recent.consultation_id
        ).update(consulted_at=now)

        response = self.client.get(
            "/api/v1/consultations/",
            {
                "date_to":
                    old_time.date().isoformat()
            },
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["consultation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [old.consultation_id],
        )

    def test_same_day_date_range_is_inclusive(self):
        consultation = self.create_consultation()

        target = timezone.now()

        Consultation.objects.filter(
            consultation_id=consultation.consultation_id
        ).update(consulted_at=target)

        date_value = target.date().isoformat()

        response = self.client.get(
            "/api/v1/consultations/",
            {
                "date_from": date_value,
                "date_to": date_value,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["count"],
            1,
        )

    def test_invalid_date_returns_canonical_400(self):
        response = self.client.get(
            "/api/v1/consultations/",
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("errors", body)

    def test_reversed_date_range_returns_empty_result(self):
        self.create_consultation()

        response = self.client.get(
            "/api/v1/consultations/",
            {
                "date_from": "2026-10-10",
                "date_to": "2026-10-01",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(
            response.json()["results"],
            [],
        )

    def test_invalid_page_returns_canonical_400(self):
        self.create_consultation()

        response = self.client.get(
            "/api/v1/consultations/",
            {"page": 999},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("errors", body)
        self.assertIn("page", body["errors"])

    def test_create_accepts_active_registrar_student(self):
        response = self.client.post(
            "/api/v1/consultations/",
            {
                "student_id": ACTIVE_STUDENT,
                "chief_complaint": "Headache",
                "assessment": "Observation",
                "treatment": "Rest",
                "notes": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()

        self.assertEqual(
            body["student_id"],
            ACTIVE_STUDENT,
        )
        self.assertEqual(
            body["chief_complaint"],
            "Headache",
        )
        self.assertEqual(
            Consultation.objects.count(),
            1,
        )

    def test_create_requires_student_id(self):
        response = self.client.post(
            "/api/v1/consultations/",
            {
                "chief_complaint": "Headache",
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "student_id",
            body["errors"],
        )

    def test_create_requires_nonblank_chief_complaint(self):
        response = self.client.post(
            "/api/v1/consultations/",
            {
                "student_id": ACTIVE_STUDENT,
                "chief_complaint": "   ",
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "chief_complaint",
            body["errors"],
        )

    def test_create_rejects_missing_registrar_student_with_404(self):
        response = self.client.post(
            "/api/v1/consultations/",
            {
                "student_id": MISSING_STUDENT,
                "chief_complaint": "Headache",
            },
            format="json",
        )

        self.assert_problem(response, 404)

        self.assertEqual(
            Consultation.objects.count(),
            0,
        )

    def test_create_rejects_inactive_registrar_student_with_422(self):
        response = self.client.post(
            "/api/v1/consultations/",
            {
                "student_id": INACTIVE_STUDENT,
                "chief_complaint": "Headache",
            },
            format="json",
        )

        self.assert_problem(response, 422)

        self.assertEqual(
            Consultation.objects.count(),
            0,
        )

    def test_retrieve_existing_consultation(self):
        consultation = self.create_consultation()

        response = self.client.get(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["consultation_id"],
            consultation.consultation_id,
        )

    def test_retrieve_missing_consultation_returns_404(self):
        response = self.client.get(
            "/api/v1/consultations/999999/"
        )

        self.assert_problem(response, 404)

    def test_put_updates_consultation_and_student(self):
        consultation = self.create_consultation()

        response = self.client.put(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            ),
            {
                "student_id":
                    SECOND_ACTIVE_STUDENT,
                "chief_complaint":
                    "Updated complaint",
                "assessment":
                    "Updated assessment",
                "treatment":
                    "Updated treatment",
                "notes":
                    "Updated notes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        consultation.refresh_from_db()

        self.assertEqual(
            consultation.student_id,
            SECOND_ACTIVE_STUDENT,
        )
        self.assertEqual(
            consultation.chief_complaint,
            "Updated complaint",
        )

    def test_put_rejects_inactive_student(self):
        consultation = self.create_consultation()

        response = self.client.put(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            ),
            {
                "student_id":
                    INACTIVE_STUDENT,
                "chief_complaint":
                    "Updated complaint",
            },
            format="json",
        )

        self.assert_problem(response, 422)

        consultation.refresh_from_db()

        self.assertEqual(
            consultation.student_id,
            ACTIVE_STUDENT,
        )

    def test_patch_updates_selected_field(self):
        consultation = self.create_consultation(
            notes="Original notes"
        )

        response = self.client.patch(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            ),
            {
                "notes": "Updated notes",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        consultation.refresh_from_db()

        self.assertEqual(
            consultation.notes,
            "Updated notes",
        )

    def test_patch_rejects_empty_payload(self):
        consultation = self.create_consultation()

        response = self.client.patch(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            ),
            {},
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

    def test_patch_revalidates_changed_student(self):
        consultation = self.create_consultation()

        response = self.client.patch(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            ),
            {
                "student_id":
                    MISSING_STUDENT,
            },
            format="json",
        )

        self.assert_problem(response, 404)

        consultation.refresh_from_db()

        self.assertEqual(
            consultation.student_id,
            ACTIVE_STUDENT,
        )

    def test_delete_removes_consultation(self):
        consultation = self.create_consultation()

        response = self.client.delete(
            (
                "/api/v1/consultations/"
                f"{consultation.consultation_id}/"
            )
        )

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            Consultation.objects.filter(
                consultation_id=(
                    consultation.consultation_id
                )
            ).exists()
        )

    def test_delete_missing_consultation_returns_404(self):
        response = self.client.delete(
            "/api/v1/consultations/999999/"
        )

        self.assert_problem(response, 404)
