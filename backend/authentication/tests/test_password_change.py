from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase


User = get_user_model()
URL = "/api/auth/password/change/"
OLD = "OriginalClinic!93826"
NEW = "DifferentWellness!59428"


class PasswordChangeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="password_staff", password=OLD)
        group, _ = Group.objects.get_or_create(name="CLINIC_STAFF")
        cls.user.groups.add(group)
        cls.other_user = User.objects.create_user(username="another_staff", password=OLD)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.token = self.client.get("/api/auth/csrf/").json()["csrfToken"]

    def change(self, **overrides):
        payload = {"current_password": OLD, "new_password": NEW, "confirm_password": NEW}
        payload.update(overrides)
        return self.client.post(URL, payload, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)

    def assert_unchanged(self):
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD))

    def test_change_hashes_password_and_keeps_current_session(self):
        previous_session = self.client.cookies["sessionid"].value
        response = self.change(user_id=self.other_user.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Your password has been changed."})
        self.user.refresh_from_db()
        self.other_user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW))
        self.assertFalse(self.user.check_password(OLD))
        self.assertNotEqual(self.user.password, NEW)
        self.assertTrue(self.other_user.check_password(OLD))
        self.assertNotEqual(self.client.cookies["sessionid"].value, previous_session)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertFalse(Client().login(username=self.user.username, password=OLD))
        self.assertTrue(Client().login(username=self.user.username, password=NEW))

    def test_other_sessions_are_invalidated(self):
        other = Client()
        other.force_login(self.user)
        self.assertEqual(self.change().status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_authentication_is_required(self):
        response = Client(enforce_csrf_checks=True).post(URL, {}, content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assert_unchanged()

    def test_csrf_is_required(self):
        response = self.client.post(URL, {"current_password": OLD, "new_password": NEW, "confirm_password": NEW}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assert_unchanged()

    def test_incorrect_current_password_is_a_field_error(self):
        response = self.change(current_password="IncorrectSecret!123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("current_password", response.json()["errors"])
        self.assertNotIn("IncorrectSecret!123", response.content.decode())
        self.assert_unchanged()

    def test_confirmation_must_match(self):
        response = self.change(confirm_password="SomethingElse!123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_password", response.json()["errors"])
        self.assert_unchanged()

    def test_new_password_must_differ(self):
        response = self.change(new_password=OLD, confirm_password=OLD)
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.json()["errors"])
        self.assert_unchanged()

    def test_django_password_validators_are_applied(self):
        for password in ["short", "password", "123456789012", "password_staff"]:
            with self.subTest(password=password):
                response = self.change(new_password=password, confirm_password=password)
                self.assertEqual(response.status_code, 400)
                self.assertIn("new_password", response.json()["errors"])
                self.assert_unchanged()

    def test_missing_and_blank_fields_are_rejected(self):
        for payload in [{}, {"current_password": "", "new_password": "", "confirm_password": ""}]:
            response = self.client.post(URL, payload, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(set(response.json()["errors"]), {"current_password", "new_password", "confirm_password"})
            self.assert_unchanged()

    def test_password_whitespace_is_not_trimmed(self):
        password = "  DeliberatelySpaced!84720  "
        self.assertEqual(self.change(new_password=password, confirm_password=password).status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(password))
        self.assertFalse(self.user.check_password(password.strip()))

    def test_oversized_password_is_rejected(self):
        response = self.change(new_password="X" * 1025, confirm_password="X" * 1025)
        self.assertEqual(response.status_code, 400)
        self.assert_unchanged()

    def test_only_post_is_supported(self):
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_schema_describes_protected_write_only_passwords(self):
        from drf_spectacular.generators import SchemaGenerator
        schema = SchemaGenerator().get_schema(request=None, public=True)
        operation = schema["paths"][URL]["post"]
        self.assertTrue(operation["security"])
        reference = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        fields = schema["components"]["schemas"][reference.split("/")[-1]]["properties"]
        self.assertTrue(all(field["writeOnly"] for field in fields.values()))
