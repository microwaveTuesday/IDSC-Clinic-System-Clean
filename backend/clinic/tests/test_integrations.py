from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase

from clinic.models import HealthStatus
from clinic.services.inventory import (
    MedicineNotFoundError,
    inventory_service,
)
from clinic.services.registrar import (
    StudentNotFoundError,
    StudentUnavailableError,
    registrar_service,
)


User = get_user_model()

PASSWORD = "TemporaryTest123!"

ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"
INACTIVE_STUDENT = "2026-0003"
MISSING_STUDENT = "9999-9999"

MEDICINE = "MED-0001"
SECOND_MEDICINE = "MED-0002"
MISSING_MEDICINE = "MED-9999"

STUDENT_FIELDS = {
    "student_id",
    "first_name",
    "last_name",
    "course",
    "section",
    "status",
}

MEDICINE_FIELDS = {
    "medicine_id",
    "name",
    "generic_name",
    "unit",
    "quantity_in_stock",
    "reorder_level",
    "is_low_stock",
    "status",
}

HEALTH_STATUS_FIELDS = {
    "student_id",
    "status",
    "remarks",
    "effective_at",
}


class IntegrationContractTests(APITestCase):
    """Permanent regression tests for Clinic integration boundaries."""

    @classmethod
    def setUpTestData(cls):
        group, _ = Group.objects.get_or_create(
            name="CLINIC_STAFF"
        )

        cls.user = User.objects.create_user(
            username="permanent_integration_user",
            password=PASSWORD,
        )
        cls.user.groups.add(group)

    def setUp(self):
        self.client.force_authenticate(
            user=self.user
        )

    def faculty_url(
        self,
        student_id=ACTIVE_STUDENT,
    ):
        return (
            "/api/v1/integrations/faculty/"
            f"health-status/{student_id}/"
        )

    def portal_url(
        self,
        student_id=ACTIVE_STUDENT,
    ):
        return (
            "/api/v1/integrations/student-portal/"
            f"health-status/{student_id}/"
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

    def test_registrar_service_uses_mock_boundary(self):
        self.assertEqual(
            registrar_service.__class__.__name__,
            "MockRegistrarService",
        )

    def test_registrar_projection_has_exact_fields(self):
        students = registrar_service.list_students()

        self.assertGreater(len(students), 0)

        for student in students:
            self.assertEqual(
                set(student),
                STUDENT_FIELDS,
            )

    def test_registrar_active_student_projection(self):
        student = registrar_service.get_student(
            ACTIVE_STUDENT
        )

        self.assertEqual(
            student["student_id"],
            ACTIVE_STUDENT,
        )
        self.assertEqual(
            student["status"],
            "ACTIVE",
        )

    def test_registrar_second_active_student_projection(self):
        student = registrar_service.get_student(
            SECOND_ACTIVE_STUDENT
        )

        self.assertEqual(
            student["student_id"],
            SECOND_ACTIVE_STUDENT,
        )
        self.assertEqual(
            student["status"],
            "ACTIVE",
        )

    def test_registrar_missing_student_raises_not_found(self):
        with self.assertRaises(
            StudentNotFoundError
        ):
            registrar_service.get_student(
                MISSING_STUDENT
            )

    def test_registrar_rejects_inactive_student_for_clinic(self):
        with self.assertRaises(
            StudentUnavailableError
        ):
            registrar_service.validate_student_for_clinic(
                INACTIVE_STUDENT
            )

    def test_inventory_service_uses_mock_boundary(self):
        self.assertEqual(
            inventory_service.__class__.__name__,
            "MockInventoryService",
        )

    def test_inventory_projection_has_exact_fields(self):
        medicines = inventory_service.list_medicines()

        self.assertGreater(len(medicines), 0)

        for medicine in medicines:
            self.assertEqual(
                set(medicine),
                MEDICINE_FIELDS,
            )

    def test_inventory_existing_medicine_projection(self):
        medicine = inventory_service.get_medicine(
            MEDICINE
        )

        self.assertEqual(
            medicine["medicine_id"],
            MEDICINE,
        )
        self.assertEqual(
            set(medicine),
            MEDICINE_FIELDS,
        )

    def test_inventory_low_stock_projection(self):
        medicine = inventory_service.get_medicine(
            SECOND_MEDICINE
        )

        self.assertTrue(
            medicine["is_low_stock"]
        )
        self.assertLessEqual(
            medicine["quantity_in_stock"],
            medicine["reorder_level"],
        )

    def test_inventory_missing_medicine_raises_not_found(self):
        with self.assertRaises(
            MedicineNotFoundError
        ):
            inventory_service.get_medicine(
                MISSING_MEDICINE
            )

    def test_faculty_returns_not_available_fallback(self):
        response = self.client.get(
            self.faculty_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            set(body),
            HEALTH_STATUS_FIELDS,
        )
        self.assertEqual(
            body,
            {
                "student_id": ACTIVE_STUDENT,
                "status": "NOT_AVAILABLE",
                "remarks": None,
                "effective_at": None,
            },
        )

    def test_student_portal_returns_not_available_fallback(self):
        response = self.client.get(
            self.portal_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            set(body),
            HEALTH_STATUS_FIELDS,
        )
        self.assertEqual(
            body,
            {
                "student_id": ACTIVE_STUDENT,
                "status": "NOT_AVAILABLE",
                "remarks": None,
                "effective_at": None,
            },
        )

    def test_faculty_returns_available_health_status(self):
        HealthStatus.objects.create(
            student_id=ACTIVE_STUDENT,
            status="RESTRICTED",
            remarks="Permanent integration test",
        )

        response = self.client.get(
            self.faculty_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            set(body),
            HEALTH_STATUS_FIELDS,
        )
        self.assertEqual(
            body["student_id"],
            ACTIVE_STUDENT,
        )
        self.assertEqual(
            body["status"],
            "RESTRICTED",
        )
        self.assertEqual(
            body["remarks"],
            "Permanent integration test",
        )
        self.assertIsNotNone(
            body["effective_at"]
        )

    def test_student_portal_returns_available_health_status(self):
        HealthStatus.objects.create(
            student_id=ACTIVE_STUDENT,
            status="UNDER_OBSERVATION",
            remarks="Permanent portal test",
        )

        response = self.client.get(
            self.portal_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            set(body),
            HEALTH_STATUS_FIELDS,
        )
        self.assertEqual(
            body["student_id"],
            ACTIVE_STUDENT,
        )
        self.assertEqual(
            body["status"],
            "UNDER_OBSERVATION",
        )
        self.assertEqual(
            body["remarks"],
            "Permanent portal test",
        )
        self.assertIsNotNone(
            body["effective_at"]
        )

    def test_integration_projection_uses_latest_health_status(self):
        HealthStatus.objects.create(
            student_id=ACTIVE_STUDENT,
            status="CLEARED",
            remarks="Older",
        )

        latest = HealthStatus.objects.create(
            student_id=ACTIVE_STUDENT,
            status="RESTRICTED",
            remarks="Latest",
        )

        response = self.client.get(
            self.faculty_url()
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()["status"],
            latest.status,
        )
        self.assertEqual(
            response.json()["remarks"],
            "Latest",
        )

    def test_faculty_missing_registrar_student_returns_404(self):
        response = self.client.get(
            self.faculty_url(
                MISSING_STUDENT
            )
        )

        self.assert_problem(
            response,
            404,
        )

    def test_student_portal_missing_registrar_student_returns_404(self):
        response = self.client.get(
            self.portal_url(
                MISSING_STUDENT
            )
        )

        self.assert_problem(
            response,
            404,
        )

    def test_faculty_endpoint_is_read_only(self):
        url = self.faculty_url()

        responses = (
            self.client.post(
                url,
                {},
                format="json",
            ),
            self.client.put(
                url,
                {},
                format="json",
            ),
            self.client.patch(
                url,
                {},
                format="json",
            ),
            self.client.delete(url),
        )

        for response in responses:
            self.assert_problem(
                response,
                405,
            )

    def test_student_portal_endpoint_is_read_only(self):
        url = self.portal_url()

        responses = (
            self.client.post(
                url,
                {},
                format="json",
            ),
            self.client.put(
                url,
                {},
                format="json",
            ),
            self.client.patch(
                url,
                {},
                format="json",
            ),
            self.client.delete(url),
        )

        for response in responses:
            self.assert_problem(
                response,
                405,
            )

    def test_faculty_requires_authentication(self):
        anonymous = APIClient()

        response = anonymous.get(
            self.faculty_url()
        )

        body = self.assert_problem(
            response,
            401,
        )

        self.assertEqual(
            body["code"],
            "not_authenticated",
        )
        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )

    def test_student_portal_requires_authentication(self):
        anonymous = APIClient()

        response = anonymous.get(
            self.portal_url()
        )

        body = self.assert_problem(
            response,
            401,
        )

        self.assertEqual(
            body["code"],
            "not_authenticated",
        )
        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )
