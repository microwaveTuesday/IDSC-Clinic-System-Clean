from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework.test import APITestCase

from clinic.tests.mock_domain import MockDomainTestMixin
from clinic.services.inventory import inventory_service


User = get_user_model()

CLINIC_STAFF = "CLINIC_STAFF"
PASSWORD = "TemporaryTest123!"

ACTIVE_STUDENT = "2026-0001"
SECOND_ACTIVE_STUDENT = "2026-0002"
INACTIVE_STUDENT = "2026-0003"
MISSING_STUDENT = "9999-9999"

MEDICINE = "MED-0001"
SECOND_MEDICINE = "MED-0002"
MISSING_MEDICINE = "MED-9999"


class MedicineDispensationContractTests(MockDomainTestMixin, APITestCase):
    """Permanent regression tests for medicine dispensing."""

    @classmethod
    def setUpTestData(cls):
        group, _ = Group.objects.get_or_create(
            name=CLINIC_STAFF
        )

        cls.user = User.objects.create_user(
            username="permanent_dispensation_staff",
            password=PASSWORD,
        )
        cls.user.groups.add(group)

    def setUp(self):
        self.reset_mock_domain()

        self.client.force_authenticate(
            user=self.user
        )

        # The Inventory service is an in-memory singleton, so preserve
        # its state around every permanent test.
        self.inventory_quantities = {
            medicine["medicine_id"]:
                medicine["quantity_in_stock"]
            for medicine in inventory_service._medicines
        }

        self.inventory_transactions = dict(
            inventory_service._transactions
        )

        self.next_transaction_number = (
            inventory_service._next_transaction_number
        )

    def tearDown(self):
        for medicine in inventory_service._medicines:
            medicine["quantity_in_stock"] = (
                self.inventory_quantities[
                    medicine["medicine_id"]
                ]
            )

        inventory_service._transactions.clear()
        inventory_service._transactions.update(
            self.inventory_transactions
        )

        inventory_service._next_transaction_number = (
            self.next_transaction_number
        )

    def stock(self, medicine_id):
        return inventory_service.get_medicine(
            medicine_id
        )["quantity_in_stock"]

    def create_via_api(
        self,
        student_id=ACTIVE_STUDENT,
        medicine_id=MEDICINE,
        quantity=1,
        reason="Permanent test",
    ):
        return self.client.post(
            "/api/v1/medicine-dispensations/",
            {
                "student_id": student_id,
                "medicine_id": medicine_id,
                "quantity": quantity,
                "reason": reason,
            },
            format="json",
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
        response = self.client.get(
            "/api/v1/medicine-dispensations/"
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

    def test_create_deducts_inventory_and_records_transaction(self):
        before = self.stock(MEDICINE)

        response = self.create_via_api(
            quantity=2,
            reason="Headache",
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()

        self.assertEqual(
            self.stock(MEDICINE),
            before - 2,
        )
        self.assertEqual(
            body["status"],
            "COMPLETED",
        )
        self.assertTrue(
            body["inventory_transaction_id"]
        )
        self.assertIsNone(
            body["rollback_transaction_id"]
        )
        self.assertEqual(
            body["reason"],
            "Headache",
        )

    def test_create_uses_empty_reason_by_default(self):
        response = self.client.post(
            "/api/v1/medicine-dispensations/",
            {
                "student_id": ACTIVE_STUDENT,
                "medicine_id": MEDICINE,
                "quantity": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["reason"],
            "",
        )

    def test_default_ordering_is_latest_dispensed_first(self):
        first_response = self.create_via_api()

        second_response = self.create_via_api(
            student_id=SECOND_ACTIVE_STUDENT,
            medicine_id=SECOND_MEDICINE,
        )

        first_id = first_response.json()[
            "dispensation_id"
        ]
        second_id = second_response.json()[
            "dispensation_id"
        ]

        now = timezone.now()
        old_time = now - timedelta(days=2)

        self.set_dispensed_at(
            first_id,
            old_time,
        )

        self.set_dispensed_at(
            second_id,
            now,
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/"
        )

        ids = [
            item["dispensation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(
            ids,
            [second_id, first_id],
        )

    def test_list_filters_by_student_id(self):
        first = self.create_via_api()
        self.create_via_api(
            student_id=SECOND_ACTIVE_STUDENT,
            medicine_id=SECOND_MEDICINE,
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"student_id": ACTIVE_STUDENT},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["results"][0][
                "dispensation_id"
            ],
            first.json()["dispensation_id"],
        )

    def test_list_filters_by_medicine_id(self):
        self.create_via_api()

        second = self.create_via_api(
            student_id=SECOND_ACTIVE_STUDENT,
            medicine_id=SECOND_MEDICINE,
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"medicine_id": SECOND_MEDICINE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["results"][0][
                "dispensation_id"
            ],
            second.json()["dispensation_id"],
        )

    def test_list_filters_by_status(self):
        response = self.create_via_api()

        dispensation_id = response.json()[
            "dispensation_id"
        ]

        self.client.post(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/rollback/"
            ),
            {},
            format="json",
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"status": "ROLLED_BACK"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["results"][0]["status"],
            "ROLLED_BACK",
        )

    def test_list_searches_reason(self):
        self.create_via_api(
            reason="Unique headache treatment"
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"search": "headache"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_date_from_filter_is_inclusive(self):
        first = self.create_via_api()
        second = self.create_via_api(
            student_id=SECOND_ACTIVE_STUDENT,
            medicine_id=SECOND_MEDICINE,
        )

        first_id = first.json()["dispensation_id"]
        second_id = second.json()["dispensation_id"]

        now = timezone.now()
        old_time = now - timedelta(days=2)

        self.set_dispensed_at(
            first_id,
            old_time,
        )

        self.set_dispensed_at(
            second_id,
            now,
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"date_from": now.date().isoformat()},
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["dispensation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(ids, [second_id])

    def test_date_to_filter_is_inclusive(self):
        first = self.create_via_api()
        second = self.create_via_api(
            student_id=SECOND_ACTIVE_STUDENT,
            medicine_id=SECOND_MEDICINE,
        )

        first_id = first.json()["dispensation_id"]
        second_id = second.json()["dispensation_id"]

        now = timezone.now()
        old_time = now - timedelta(days=2)

        self.set_dispensed_at(
            first_id,
            old_time,
        )

        self.set_dispensed_at(
            second_id,
            now,
        )

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"date_to": old_time.date().isoformat()},
        )

        self.assertEqual(response.status_code, 200)

        ids = [
            item["dispensation_id"]
            for item in response.json()["results"]
        ]

        self.assertEqual(ids, [first_id])

    def test_invalid_date_returns_canonical_400(self):
        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"date_from": "not-a-date"},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("errors", body)

    def test_reversed_date_range_returns_empty_result(self):
        self.create_via_api()

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
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
        self.create_via_api()

        response = self.client.get(
            "/api/v1/medicine-dispensations/",
            {"page": 999},
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn("page", body["errors"])

    def test_create_rejects_zero_quantity(self):
        response = self.create_via_api(
            quantity=0
        )

        body = self.assert_problem(
            response,
            400,
        )

        self.assertIn(
            "quantity",
            body["errors"],
        )

    def test_create_rejects_missing_registrar_student(self):
        before = self.stock(MEDICINE)

        response = self.create_via_api(
            student_id=MISSING_STUDENT
        )

        self.assert_problem(response, 404)
        self.assertEqual(
            self.stock(MEDICINE),
            before,
        )

    def test_create_rejects_inactive_registrar_student(self):
        before = self.stock(MEDICINE)

        response = self.create_via_api(
            student_id=INACTIVE_STUDENT
        )

        self.assert_problem(response, 422)
        self.assertEqual(
            self.stock(MEDICINE),
            before,
        )

    def test_create_rejects_missing_inventory_medicine(self):
        response = self.create_via_api(
            medicine_id=MISSING_MEDICINE
        )

        self.assert_problem(response, 404)

    def test_create_rejects_insufficient_stock(self):
        before = self.stock(SECOND_MEDICINE)

        response = self.create_via_api(
            medicine_id=SECOND_MEDICINE,
            quantity=999,
        )

        self.assert_problem(response, 422)
        self.assertEqual(
            self.stock(SECOND_MEDICINE),
            before,
        )

    def test_retrieve_existing_dispensation(self):
        created = self.create_via_api()

        dispensation_id = created.json()[
            "dispensation_id"
        ]

        response = self.client.get(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["dispensation_id"],
            dispensation_id,
        )

    def test_retrieve_missing_dispensation_returns_404(self):
        response = self.client.get(
            "/api/v1/medicine-dispensations/999999/"
        )

        self.assert_problem(response, 404)

    def test_put_is_not_exposed(self):
        created = self.create_via_api()
        dispensation_id = created.json()[
            "dispensation_id"
        ]

        response = self.client.put(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/"
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_patch_is_not_exposed(self):
        created = self.create_via_api()
        dispensation_id = created.json()[
            "dispensation_id"
        ]

        response = self.client.patch(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/"
            ),
            {"reason": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, 405)

    def test_delete_is_not_exposed(self):
        created = self.create_via_api()
        dispensation_id = created.json()[
            "dispensation_id"
        ]

        response = self.client.delete(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/"
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_rollback_restores_stock_and_records_transaction(self):
        before = self.stock(MEDICINE)

        created = self.create_via_api(
            quantity=2
        )

        dispensation_id = created.json()[
            "dispensation_id"
        ]

        self.assertEqual(
            self.stock(MEDICINE),
            before - 2,
        )

        response = self.client.post(
            (
                "/api/v1/medicine-dispensations/"
                f"{dispensation_id}/rollback/"
            ),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(
            body["status"],
            "ROLLED_BACK",
        )
        self.assertTrue(
            body["rollback_transaction_id"]
        )
        self.assertIsNotNone(
            body["rolled_back_at"]
        )
        self.assertEqual(
            self.stock(MEDICINE),
            before,
        )

    def test_duplicate_rollback_returns_409_without_stock_change(self):
        created = self.create_via_api(
            quantity=2
        )

        dispensation_id = created.json()[
            "dispensation_id"
        ]

        rollback_url = (
            "/api/v1/medicine-dispensations/"
            f"{dispensation_id}/rollback/"
        )

        first = self.client.post(
            rollback_url,
            {},
            format="json",
        )

        self.assertEqual(first.status_code, 200)

        stock_after_first = self.stock(
            MEDICINE
        )

        response = self.client.post(
            rollback_url,
            {},
            format="json",
        )

        self.assert_problem(response, 409)

        self.assertEqual(
            self.stock(MEDICINE),
            stock_after_first,
        )

    def test_rollback_missing_dispensation_returns_404(self):
        response = self.client.post(
            (
                "/api/v1/medicine-dispensations/"
                "999999/rollback/"
            ),
            {},
            format="json",
        )

        self.assert_problem(response, 404)
