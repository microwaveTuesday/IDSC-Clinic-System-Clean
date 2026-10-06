from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase


User = get_user_model()

PASSWORD = "TemporaryTest123!"

PUBLIC_URL = "/api/v1/health/"
AUTH_ONLY_URL = "/api/auth/me/"
STAFF_URL = "/api/v1/dashboard/"
ADMIN_URL = "/api/v1/users/"

FACULTY_URL = (
    "/api/v1/integrations/faculty/"
    "health-status/2026-0001/"
)

PORTAL_URL = (
    "/api/v1/integrations/student-portal/"
    "health-status/2026-0001/"
)

STAFF_ENDPOINTS = (
    "/api/v1/dashboard/",
    "/api/v1/students/",
    "/api/v1/health-records/",
    "/api/v1/consultations/",
    "/api/v1/health-statuses/",
    "/api/v1/medicines/",
    "/api/v1/medicine-dispensations/",
    "/api/v1/reports/medicine-inventory/",
)

AUTH_ONLY_ENDPOINTS = (
    AUTH_ONLY_URL,
    FACULTY_URL,
    PORTAL_URL,
)


class PermissionContractTests(APITestCase):
    """Permanent regression tests for Clinic authorization boundaries."""

    @classmethod
    def setUpTestData(cls):
        staff_group, _ = Group.objects.get_or_create(
            name="CLINIC_STAFF"
        )
        admin_group, _ = Group.objects.get_or_create(
            name="CLINIC_ADMIN"
        )

        cls.plain = User.objects.create_user(
            username="permanent_permission_plain",
            password=PASSWORD,
        )

        cls.staff = User.objects.create_user(
            username="permanent_permission_staff",
            password=PASSWORD,
        )
        cls.staff.groups.add(staff_group)

        cls.admin = User.objects.create_user(
            username="permanent_permission_admin",
            password=PASSWORD,
        )
        cls.admin.groups.add(admin_group)

    def client_for(self, user=None):
        client = APIClient()

        if user is not None:
            client.force_authenticate(user=user)

        return client

    def assert_problem(
        self,
        response,
        expected_status,
        expected_code,
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
        self.assertEqual(
            body["code"],
            expected_code,
        )

        return body

    def test_health_endpoint_is_public(self):
        response = self.client_for().get(
            PUBLIC_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_authenticated_user_can_access_me(self):
        response = self.client_for(
            self.plain
        ).get(
            AUTH_ONLY_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_authenticated_user_can_access_faculty_integration(self):
        response = self.client_for(
            self.plain
        ).get(
            FACULTY_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_authenticated_user_can_access_student_portal_integration(self):
        response = self.client_for(
            self.plain
        ).get(
            PORTAL_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_anonymous_auth_only_endpoints_return_401(self):
        client = self.client_for()

        for url in AUTH_ONLY_ENDPOINTS:
            response = client.get(url)

            self.assert_problem(
                response,
                401,
                "not_authenticated",
            )

            self.assertEqual(
                response.get(
                    "WWW-Authenticate"
                ),
                "Session",
            )

    def test_anonymous_staff_endpoint_returns_401(self):
        response = self.client_for().get(
            STAFF_URL
        )

        self.assert_problem(
            response,
            401,
            "not_authenticated",
        )

        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )

    def test_plain_user_is_forbidden_from_staff_endpoint(self):
        response = self.client_for(
            self.plain
        ).get(
            STAFF_URL
        )

        self.assert_problem(
            response,
            403,
            "permission_denied",
        )

        self.assertIsNone(
            response.get(
                "WWW-Authenticate"
            )
        )

    def test_clinic_staff_can_access_staff_endpoint(self):
        response = self.client_for(
            self.staff
        ).get(
            STAFF_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_clinic_admin_can_access_staff_endpoint(self):
        response = self.client_for(
            self.admin
        ).get(
            STAFF_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_admin_inherits_staff_access_without_staff_group(self):
        self.assertEqual(
            list(
                self.admin.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            ["CLINIC_ADMIN"],
        )

        for url in STAFF_ENDPOINTS:
            response = self.client_for(
                self.admin
            ).get(url)

            self.assertEqual(
                response.status_code,
                200,
                msg=url,
            )

    def test_plain_user_is_forbidden_from_all_staff_endpoints(self):
        client = self.client_for(
            self.plain
        )

        for url in STAFF_ENDPOINTS:
            response = client.get(url)

            self.assert_problem(
                response,
                403,
                "permission_denied",
            )

    def test_clinic_staff_can_access_all_staff_endpoints(self):
        client = self.client_for(
            self.staff
        )

        for url in STAFF_ENDPOINTS:
            response = client.get(url)

            self.assertEqual(
                response.status_code,
                200,
                msg=url,
            )

    def test_anonymous_admin_endpoint_returns_401(self):
        response = self.client_for().get(
            ADMIN_URL
        )

        self.assert_problem(
            response,
            401,
            "not_authenticated",
        )

        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )

    def test_plain_user_is_forbidden_from_admin_endpoint(self):
        response = self.client_for(
            self.plain
        ).get(
            ADMIN_URL
        )

        self.assert_problem(
            response,
            403,
            "permission_denied",
        )

    def test_clinic_staff_is_forbidden_from_admin_endpoint(self):
        response = self.client_for(
            self.staff
        ).get(
            ADMIN_URL
        )

        self.assert_problem(
            response,
            403,
            "permission_denied",
        )

    def test_clinic_admin_can_access_admin_endpoint(self):
        response = self.client_for(
            self.admin
        ).get(
            ADMIN_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_role_group_membership_is_exact(self):
        self.assertEqual(
            list(
                self.plain.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            [],
        )

        self.assertEqual(
            list(
                self.staff.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            ["CLINIC_STAFF"],
        )

        self.assertEqual(
            list(
                self.admin.groups.values_list(
                    "name",
                    flat=True,
                )
            ),
            ["CLINIC_ADMIN"],
        )
