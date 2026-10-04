from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APITestCase

from clinic.tests.mock_domain import MockDomainTestMixin


User = get_user_model()

CLINIC_STAFF = "CLINIC_STAFF"
PASSWORD = "TemporaryTest123!"

ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"
INACTIVE_STUDENT = "2026-0003"
MISSING_STUDENT = "9999-9999"


class HealthStatusContractTests(MockDomainTestMixin, APITestCase):
    """Permanent regression tests for Clinic health-status records."""

    @classmethod
    def setUpTestData(cls):
        group, _ = Group.objects.get_or_create(
            name=CLINIC_STAFF
        )

        cls.user = User.objects.create_user(
            username="permanent_health_status_staff",
            password=PASSWORD,
        )
        cls.user.groups.add(group)

    def setUp(self):
        self.reset_mock_domain()

        self.client.force_authenticate(
            user=self.user
        )

    def create_status(
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

        return self.create_mock_health_status(
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
        self.create_status()

        response = self.client.get(
            "/api/v1/health-statuses/"
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

    def test_default_ordering_is_latest_effective_status_first(self):
        first = self.create_status()

        second = self.create_status(
            student_id=SECOND_ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        old_time = timezone.now() - timedelta(days=2)
        new_time = timezone.now()

        self.set_effective_at(
            first.status_id,
            old_time,
        )

        self.set_effective_at(
            second.status_id,
            new_time,
        )

        response = self.client.get(
            "/api/v1/health-statuses/"
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["status_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [
                second.status_id,
                first.status_id,
            ],
        )

    def test_list_filters_by_student_id(self):
        first = self.create_status()

        self.create_status(
            student_id=SECOND_ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        response = self.client.get(
            "/api/v1/health-statuses/",
            {"student_id": ACTIVE_STUDENT},
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["status_id"],
            first.status_id,
        )

    def test_list_filters_by_status(self):
        self.create_status(
            status="CLEARED"
        )

        restricted = self.create_status(
            student_id=SECOND_ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        response = self.client.get(
            "/api/v1/health-statuses/",
            {"status": "RESTRICTED"},
        )

        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["status_id"],
            restricted.status_id,
        )

    def test_list_supports_documented_ordering(self):
        first = self.create_status(
            student_id=SECOND_ACTIVE_STUDENT
        )

        second = self.create_status(
            student_id=ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        response = self.client.get(
            "/api/v1/health-statuses/",
            {"ordering": "student_id"},
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["status_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [
                second.status_id,
                first.status_id,
            ],
        )

    def test_date_from_filter_is_inclusive(self):
        old = self.create_status()

        recent = self.create_status(
            student_id=SECOND_ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        now = timezone.now()
        old_time = now - timedelta(days=2)

        self.set_effective_at(
            old.status_id,
            old_time,
        )

        self.set_effective_at(
            recent.status_id,
            now,
        )

        response = self.client.get(
            "/api/v1/health-statuses/",
            {
                "date_from":
                    now.date().isoformat()
            },
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["status_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [recent.status_id],
        )

    def test_date_to_filter_is_inclusive(self):
        old = self.create_status()

        recent = self.create_status(
            student_id=SECOND_ACTIVE_STUDENT,
            status="RESTRICTED",
        )

        now = timezone.now()
        old_time = now - timedelta(days=2)

        self.set_effective_at(
            old.status_id,
            old_time,
        )

        self.set_effective_at(
            recent.status_id,
            now,
        )

        response = self.client.get(
            "/api/v1/health-statuses/",
            {
                "date_to":
                    old_time.date().isoformat()
            },
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["status_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [old.status_id],
        )

    def test_same_day_date_range_is_inclusive(self):
        status = self.create_status()
        target = timezone.now()

        self.set_effective_at(
            status.status_id,
            target,
        )

        date_value = target.date().isoformat()

        response = self.client.get(
            "/api/v1/health-statuses/",
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
            "/api/v1/health-statuses/",
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("errors", body)

    def test_reversed_date_range_returns_empty_result(self):
        self.create_status()

        response = self.client.get(
            "/api/v1/health-statuses/",
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
        self.create_status()

        response = self.client.get(
            "/api/v1/health-statuses/",
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
            "/api/v1/health-statuses/",
            {
                "student_id": ACTIVE_STUDENT,
                "status": "CLEARED",
                "remarks": "Cleared",
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
            body["status"],
            "CLEARED",
        )
        self.assertEqual(
            self.health_status_count(),
            1,
        )

    def test_create_requires_student_id(self):
        response = self.client.post(
            "/api/v1/health-statuses/",
            {
                "status": "CLEARED",
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

    def test_create_requires_status(self):
        response = self.client.post(
            "/api/v1/health-statuses/",
            {
                "student_id": ACTIVE_STUDENT,
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "status",
            body["errors"],
        )

    def test_create_rejects_invalid_status(self):
        response = self.client.post(
            "/api/v1/health-statuses/",
            {
                "student_id": ACTIVE_STUDENT,
                "status": "INVALID",
            },
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "status",
            body["errors"],
        )

    def test_create_rejects_missing_registrar_student_with_404(self):
        response = self.client.post(
            "/api/v1/health-statuses/",
            {
                "student_id": MISSING_STUDENT,
                "status": "CLEARED",
            },
            format="json",
        )

        self.assert_problem(response, 404)

        self.assertEqual(
            self.health_status_count(),
            0,
        )

    def test_create_rejects_inactive_registrar_student_with_422(self):
        response = self.client.post(
            "/api/v1/health-statuses/",
            {
                "student_id": INACTIVE_STUDENT,
                "status": "RESTRICTED",
            },
            format="json",
        )

        self.assert_problem(response, 422)

        self.assertEqual(
            self.health_status_count(),
            0,
        )

    def test_retrieve_existing_health_status(self):
        status = self.create_status()

        response = self.client.get(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status_id"],
            status.status_id,
        )

    def test_retrieve_missing_health_status_returns_404(self):
        response = self.client.get(
            "/api/v1/health-statuses/999999/"
        )

        self.assert_problem(response, 404)

    def test_put_updates_health_status_and_student(self):
        status = self.create_status()

        response = self.client.put(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            ),
            {
                "student_id":
                    SECOND_ACTIVE_STUDENT,
                "status":
                    "UNDER_OBSERVATION",
                "remarks":
                    "Observe symptoms",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        status.refresh_from_db()

        self.assertEqual(
            status.student_id,
            SECOND_ACTIVE_STUDENT,
        )
        self.assertEqual(
            status.status,
            "UNDER_OBSERVATION",
        )

    def test_put_rejects_inactive_student(self):
        status = self.create_status()

        response = self.client.put(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            ),
            {
                "student_id":
                    INACTIVE_STUDENT,
                "status":
                    "RESTRICTED",
            },
            format="json",
        )

        self.assert_problem(response, 422)

        status.refresh_from_db()

        self.assertEqual(
            status.student_id,
            ACTIVE_STUDENT,
        )

    def test_patch_updates_selected_field(self):
        status = self.create_status(
            remarks="Original remarks"
        )

        response = self.client.patch(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            ),
            {
                "remarks": "Updated remarks",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        status.refresh_from_db()

        self.assertEqual(
            status.remarks,
            "Updated remarks",
        )

    def test_patch_rejects_empty_payload(self):
        status = self.create_status()

        response = self.client.patch(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            ),
            {},
            format="json",
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("errors", body)

    def test_patch_revalidates_changed_student(self):
        status = self.create_status()

        response = self.client.patch(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            ),
            {
                "student_id":
                    MISSING_STUDENT,
            },
            format="json",
        )

        self.assert_problem(response, 404)

        status.refresh_from_db()

        self.assertEqual(
            status.student_id,
            ACTIVE_STUDENT,
        )

    def test_delete_removes_health_status(self):
        status = self.create_status()

        response = self.client.delete(
            (
                "/api/v1/health-statuses/"
                f"{status.status_id}/"
            )
        )

        self.assertEqual(response.status_code, 204)

        self.assertFalse(
            self.health_status_exists(
                status.status_id
            )
        )
