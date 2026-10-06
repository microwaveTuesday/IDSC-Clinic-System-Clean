from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient, APITestCase

from clinic.services.inventory import inventory_service


User = get_user_model()

PASSWORD = "TemporaryTest123!"

CLINIC_VISITS_URL = "/api/v1/reports/clinic-visits/"
HEALTH_RECORDS_URL = "/api/v1/reports/health-records/"
MEDICINE_INVENTORY_URL = "/api/v1/reports/medicine-inventory/"
MEDICINE_DISPENSATIONS_URL = (
    "/api/v1/reports/medicine-dispensations/"
)

REPORT_URLS = (
    CLINIC_VISITS_URL,
    HEALTH_RECORDS_URL,
    MEDICINE_INVENTORY_URL,
    MEDICINE_DISPENSATIONS_URL,
)


class ReportContractTests(APITestCase):
    """Permanent regression tests for Clinic report contracts."""

    @classmethod
    def setUpTestData(cls):
        staff_group, _ = Group.objects.get_or_create(
            name="CLINIC_STAFF"
        )

        cls.staff = User.objects.create_user(
            username="permanent_report_staff",
            password=PASSWORD,
        )
        cls.staff.groups.add(staff_group)

        cls.no_role = User.objects.create_user(
            username="permanent_report_no_role",
            password=PASSWORD,
        )

    def setUp(self):
        self.client.force_authenticate(
            user=self.staff
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

    def test_clinic_visits_empty_report_envelope(self):
        response = self.client.get(
            CLINIC_VISITS_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "total_visits": 0,
                "results": [],
            },
        )

    def test_health_records_empty_report_envelope(self):
        response = self.client.get(
            HEALTH_RECORDS_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "total_health_records": 0,
                "results": [],
            },
        )

    def test_medicine_dispensations_empty_report_envelope(self):
        response = self.client.get(
            MEDICINE_DISPENSATIONS_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "total_dispensations": 0,
                "total_quantity_dispensed": 0,
                "results": [],
            },
        )

    def test_medicine_inventory_report_aggregates_baseline(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["total_medicines"],
            3,
        )
        self.assertEqual(
            body["total_stock"],
            115,
        )
        self.assertEqual(
            body["low_stock_medicines"],
            2,
        )
        self.assertEqual(
            len(body["results"]),
            3,
        )

    def test_medicine_inventory_report_preserves_projection_fields(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        expected_fields = {
            "medicine_id",
            "name",
            "generic_name",
            "unit",
            "quantity_in_stock",
            "reorder_level",
            "is_low_stock",
            "status",
        }

        for medicine in response.json()["results"]:
            self.assertEqual(
                set(medicine),
                expected_fields,
            )

    def test_medicine_inventory_low_stock_true_filter(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL,
            {"low_stock": "true"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["total_medicines"],
            2,
        )
        self.assertEqual(
            body["total_stock"],
            15,
        )
        self.assertEqual(
            body["low_stock_medicines"],
            2,
        )
        self.assertEqual(
            {
                item["medicine_id"]
                for item in body["results"]
            },
            {
                "MED-0002",
                "MED-0003",
            },
        )

    def test_medicine_inventory_low_stock_false_filter(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL,
            {"low_stock": "false"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["total_medicines"],
            1,
        )
        self.assertEqual(
            body["total_stock"],
            100,
        )
        self.assertEqual(
            body["low_stock_medicines"],
            0,
        )
        self.assertEqual(
            body["results"][0]["medicine_id"],
            "MED-0001",
        )

    def test_medicine_inventory_status_filter(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL,
            {"status": "ACTIVE"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["total_medicines"],
            3,
        )

        self.assertTrue(
            all(
                item["status"] == "ACTIVE"
                for item in body["results"]
            )
        )

    def test_medicine_inventory_invalid_low_stock_returns_400(self):
        response = self.client.get(
            MEDICINE_INVENTORY_URL,
            {"low_stock": "maybe"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertEqual(
            body["code"],
            "bad_request",
        )
        self.assertIn(
            "low_stock",
            body["errors"],
        )

    def test_clinic_visits_invalid_date_returns_400(self):
        response = self.client.get(
            CLINIC_VISITS_URL,
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_from",
            body["errors"],
        )

    def test_health_records_invalid_date_returns_400(self):
        response = self.client.get(
            HEALTH_RECORDS_URL,
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_from",
            body["errors"],
        )

    def test_medicine_dispensations_invalid_date_returns_400(self):
        response = self.client.get(
            MEDICINE_DISPENSATIONS_URL,
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_from",
            body["errors"],
        )

    def test_clinic_visits_reversed_date_range_returns_400(self):
        response = self.client.get(
            CLINIC_VISITS_URL,
            {
                "date_from": "2026-10-10",
                "date_to": "2026-10-01",
            },
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_range",
            body["errors"],
        )

    def test_health_records_reversed_date_range_returns_400(self):
        response = self.client.get(
            HEALTH_RECORDS_URL,
            {
                "date_from": "2026-10-10",
                "date_to": "2026-10-01",
            },
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_range",
            body["errors"],
        )

    def test_medicine_dispensations_reversed_date_range_returns_400(self):
        response = self.client.get(
            MEDICINE_DISPENSATIONS_URL,
            {
                "date_from": "2026-10-10",
                "date_to": "2026-10-01",
            },
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "date_range",
            body["errors"],
        )

    def test_report_endpoints_are_read_only(self):
        for url in REPORT_URLS:
            response = self.client.post(
                url,
                {},
                format="json",
            )

            body = self.assert_problem(
                response,
                405,
            )

            self.assertEqual(
                body["code"],
                "method_not_allowed",
            )

    def test_report_endpoints_require_authentication(self):
        anonymous = APIClient()

        for url in REPORT_URLS:
            response = anonymous.get(url)

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

    def test_report_endpoints_require_clinic_staff_role(self):
        forbidden = APIClient()
        forbidden.force_authenticate(
            user=self.no_role
        )

        for url in REPORT_URLS:
            response = forbidden.get(url)

            body = self.assert_problem(
                response,
                403,
            )

            self.assertEqual(
                body["code"],
                "permission_denied",
            )

    def test_report_requests_do_not_mutate_inventory_baseline(self):
        before = {
            medicine_id:
                inventory_service.get_medicine(
                    medicine_id
                )["quantity_in_stock"]
            for medicine_id in (
                "MED-0001",
                "MED-0002",
                "MED-0003",
            )
        }

        self.client.get(
            MEDICINE_INVENTORY_URL
        )
        self.client.get(
            MEDICINE_INVENTORY_URL,
            {"low_stock": "true"},
        )

        after = {
            medicine_id:
                inventory_service.get_medicine(
                    medicine_id
                )["quantity_in_stock"]
            for medicine_id in (
                "MED-0001",
                "MED-0002",
                "MED-0003",
            )
        }

        self.assertEqual(
            after,
            before,
        )
