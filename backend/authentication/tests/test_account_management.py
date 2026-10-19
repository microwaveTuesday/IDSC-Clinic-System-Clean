from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase

User = get_user_model()
PASSWORD = "ClinicAccount!83047"
NEW_PASSWORD = "DifferentAdmin!28496"
USERNAME_URL = "/api/auth/username/change/"
ADMINS_URL = "/api/v1/admins/"


class AccountManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_group, _ = Group.objects.get_or_create(name="CLINIC_ADMIN")
        staff_group, _ = Group.objects.get_or_create(name="CLINIC_STAFF")
        cls.admin = User.objects.create_user(username="account_admin", password=PASSWORD)
        cls.admin.groups.add(admin_group)
        cls.staff = User.objects.create_user(username="account_staff", password=PASSWORD)
        cls.staff.groups.add(staff_group)
        cls.superuser = User.objects.create_superuser(username="account_root", password=PASSWORD)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.admin)
        self.token = self.client.get("/api/auth/csrf/").json()["csrfToken"]

    def post(self, url, payload):
        return self.client.post(url, payload, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)

    def rename(self, **overrides):
        payload = {"new_username": "renamed_admin", "current_password": PASSWORD}
        payload.update(overrides)
        return self.post(USERNAME_URL, payload)

    def create_admin(self, **overrides):
        payload = {"username": "additional_admin", "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD, "current_password": PASSWORD, "first_name": "Another", "email": "admin@example.test"}
        payload.update(overrides)
        return self.post(ADMINS_URL, payload)

    def test_admin_can_rename_self_and_session_survives(self):
        response = self.rename(user_id=self.staff.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "renamed_admin")
        self.assertNotIn("password", response.json())
        self.assertEqual(self.client.get("/api/auth/me/").json()["username"], "renamed_admin")
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.username, "account_staff")
        self.assertFalse(Client().login(username="account_admin", password=PASSWORD))
        self.assertTrue(Client().login(username="renamed_admin", password=PASSWORD))

    def test_staff_can_rename_self_without_becoming_admin(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.rename().status_code, 200)
        self.assertEqual(self.client.get(ADMINS_URL).status_code, 403)
        self.staff.refresh_from_db()
        self.assertFalse(self.staff.is_superuser)
        self.assertFalse(self.staff.groups.filter(name="CLINIC_ADMIN").exists())

    def test_wrong_password_prevents_rename(self):
        response = self.rename(current_password="Incorrect!123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", response.json()["errors"])
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, "account_admin")

    def test_duplicate_usernames_are_rejected_case_insensitively(self):
        for name in ["account_staff", "ACCOUNT_STAFF"]:
            self.assertEqual(self.rename(new_username=name).status_code, 400)

    def test_invalid_blank_long_and_unchanged_usernames_are_rejected(self):
        for name in ["", "   ", "invalid name!", "X" * 151, "account_admin"]:
            with self.subTest(name=name):
                self.assertEqual(self.rename(new_username=name).status_code, 400)

    def test_username_is_trimmed_and_unicode_normalized(self):
        response = self.rename(new_username="  Ａlpha_admin  ")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "Alpha_admin")

    def test_rename_requires_authentication_and_csrf(self):
        self.assertEqual(Client().post(USERNAME_URL, {}, content_type="application/json").status_code, 401)
        self.assertEqual(self.client.post(USERNAME_URL, {"current_password": PASSWORD, "new_username": "changed"}, content_type="application/json").status_code, 403)

    def test_rename_requires_both_fields_and_post(self):
        self.assertEqual(self.post(USERNAME_URL, {}).status_code, 400)
        self.assertEqual(self.client.get(USERNAME_URL).status_code, 405)

    def test_owner_can_create_admin_without_superuser_flags(self):
        self.client.force_login(self.superuser)
        response = self.create_admin(is_superuser=True, is_staff=True, role="STAFF")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["role"], "ADMIN")
        self.assertNotIn("password", response.json())
        self.assertNotIn("current_password", response.json())
        user = User.objects.get(username="additional_admin")
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertNotEqual(user.password, NEW_PASSWORD)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.groups.filter(name="CLINIC_ADMIN").exists())
        self.assertFalse(user.groups.filter(name="CLINIC_STAFF").exists())
        other = Client()
        self.assertTrue(other.login(username=user.username, password=NEW_PASSWORD))
        self.assertEqual(other.get("/api/v1/dashboard/").status_code, 200)
        self.assertEqual(other.get("/api/v1/users/").status_code, 200)
        self.assertEqual(other.get(ADMINS_URL).status_code, 403)

    def test_staff_cannot_create_or_list_admins(self):
        self.client.force_login(self.staff)
        before = User.objects.count()
        self.assertEqual(self.create_admin().status_code, 403)
        self.assertEqual(self.client.get(ADMINS_URL).status_code, 403)
        self.assertEqual(User.objects.count(), before)

    def test_admin_creation_requires_authentication_and_csrf(self):
        self.assertEqual(Client().post(ADMINS_URL, {}, content_type="application/json").status_code, 401)
        self.assertEqual(self.client.post(ADMINS_URL, {}, content_type="application/json").status_code, 403)

    def test_admin_creation_requires_actor_password(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.create_admin(current_password="Incorrect!123").status_code, 400)
        self.assertFalse(User.objects.filter(username="additional_admin").exists())

    def test_admin_creation_validates_confirmation_and_strength(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.create_admin(confirm_password="Different!123").status_code, 400)
        for value in ["short", "password", "123456789012", "additional_admin"]:
            self.assertEqual(self.create_admin(password=value, confirm_password=value).status_code, 400)
        self.assertFalse(User.objects.filter(username="additional_admin").exists())

    def test_admin_creation_rejects_duplicate_and_invalid_usernames(self):
        self.client.force_login(self.superuser)
        for value in ["account_admin", "ACCOUNT_ADMIN", "invalid name!", ""]:
            self.assertEqual(self.create_admin(username=value).status_code, 400)

    def test_admin_creation_requires_fields(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.post(ADMINS_URL, {}).status_code, 400)

    def test_owner_directory_excludes_owners_even_with_admin_group(self):
        self.client.force_login(self.superuser)
        self.superuser.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        response = self.client.get(ADMINS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({row["username"] for row in response.json()}, {"account_admin"})
        self.assertEqual(len(response.json()), 1)

    def test_new_admin_cannot_create_another_admin(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.create_admin().status_code, 201)
        self.client.force_login(User.objects.get(username="additional_admin"))
        self.assertEqual(self.create_admin(username="third_admin", current_password=NEW_PASSWORD).status_code, 403)

    def test_staff_creation_endpoint_cannot_promote_a_new_user(self):
        response = self.post("/api/v1/users/", {"username": "regular_staff", "password": NEW_PASSWORD, "role": "ADMIN", "is_superuser": True})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["role"], "STAFF")
        self.assertFalse(User.objects.get(username="regular_staff").is_superuser)
