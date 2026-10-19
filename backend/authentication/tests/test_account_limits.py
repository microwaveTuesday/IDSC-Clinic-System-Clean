from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "AccountLimit!49283"


class AccountLimitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(username="limits_owner", password=PASSWORD)
        cls.admin_group = Group.objects.get(name="CLINIC_ADMIN")
        cls.staff_group = Group.objects.get(name="CLINIC_STAFF")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def admin(self, number, active=True):
        user = User.objects.create_user(username=f"limits_admin_{number}", is_active=active)
        user.groups.add(self.admin_group)
        return user

    def create_admin(self, number):
        return self.client.post("/api/v1/admins/", {"username": f"created_admin_{number}", "current_password": PASSWORD, "password": "CreatedAccount!58372", "confirm_password": "CreatedAccount!58372"}, format="json")

    def staff(self, number):
        user = User.objects.create_user(username=f"limits_staff_{number:02}")
        user.groups.add(self.staff_group)
        return user

    def test_fifth_admin_allowed_sixth_rejected_without_account_created(self):
        for i in range(4): self.admin(i)
        self.assertEqual(self.create_admin(5).status_code, 201)
        response = self.create_admin(6)
        self.assertEqual(response.status_code, 409)
        self.assertIn("Delete", response.json()["detail"])
        self.assertFalse(User.objects.filter(username="created_admin_6").exists())
        self.assertEqual(User.objects.filter(groups=self.admin_group, is_superuser=False).count(), 5)

    def test_inactive_admin_counts_and_deactivation_does_not_free_slot(self):
        admins = [self.admin(i) for i in range(5)]
        self.assertEqual(self.client.post(f"/api/v1/admins/{admins[0].pk}/deactivate/").status_code, 200)
        self.assertEqual(self.create_admin(6).status_code, 409)

    def test_delete_frees_slot_for_replacement_admin(self):
        admins = [self.admin(i, active=i != 0) for i in range(5)]
        self.assertEqual(self.create_admin(6).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/v1/admins/{admins[0].pk}/", {"current_password": PASSWORD}, format="json").status_code, 204)
        self.assertEqual(self.create_admin(6).status_code, 201)

    def test_owner_does_not_count_even_with_admin_group(self):
        self.owner.groups.add(self.admin_group)
        for i in range(4): self.admin(i)
        self.assertEqual(self.create_admin(5).status_code, 201)

    def test_existing_over_limit_accounts_preserved_and_creation_blocked(self):
        for i in range(6): self.admin(i)
        self.assertEqual(self.create_admin(7).status_code, 409)
        self.assertEqual(User.objects.filter(groups=self.admin_group).count(), 6)

    def test_staff_default_page_has_ten_next_page_contains_remaining(self):
        expected = [self.staff(i).pk for i in range(13)]
        first = self.client.get("/api/v1/users/").json()
        second = self.client.get("/api/v1/users/?page=2").json()
        self.assertEqual((first["count"], first["page_size"], first["total_pages"]), (13, 10, 2))
        self.assertEqual([u["user_id"] for u in first["results"]], expected[:10])
        self.assertEqual([u["user_id"] for u in second["results"]], expected[10:])
        self.assertEqual(second["page"], 2)

    def test_staff_page_size_cannot_exceed_ten(self):
        for i in range(11): self.staff(i)
        for size in [11, 20, 100, 999]:
            body = self.client.get(f"/api/v1/users/?page_size={size}").json()
            self.assertEqual(body["page_size"], 10)
            self.assertEqual(len(body["results"]), 10)
        self.assertEqual(self.client.get("/api/v1/users/?page_size=5").json()["page_size"], 5)

    def test_empty_and_exactly_ten_staff_have_one_page(self):
        empty = self.client.get("/api/v1/users/").json()
        self.assertEqual((empty["count"], empty["total_pages"], empty["results"]), (0, 1, []))
        for i in range(10): self.staff(i)
        body = self.client.get("/api/v1/users/").json()
        self.assertEqual((len(body["results"]), body["total_pages"]), (10, 1))

    def test_deleted_last_row_reduces_page_count(self):
        staff = [self.staff(i) for i in range(11)]
        self.assertEqual(self.client.delete(f"/api/v1/users/{staff[-1].pk}/", {"current_password": PASSWORD}, format="json").status_code, 204)
        self.assertEqual(self.client.get("/api/v1/users/").json()["total_pages"], 1)
        self.assertEqual(self.client.get("/api/v1/users/?page=2").status_code, 400)
