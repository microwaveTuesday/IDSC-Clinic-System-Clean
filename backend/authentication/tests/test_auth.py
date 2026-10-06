from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from rest_framework.test import APITestCase


User = get_user_model()

CLINIC_STAFF = "CLINIC_STAFF"
PASSWORD = "TemporaryTest123!"


class AuthenticationContractTests(APITestCase):
    """Permanent regression tests for the Clinic session-authentication contract."""

    @classmethod
    def setUpTestData(cls):
        cls.staff_group, _ = Group.objects.get_or_create(
            name=CLINIC_STAFF
        )

        cls.user = User.objects.create_user(
            username="permanent_auth_staff",
            password=PASSWORD,
            email="clinic@example.test",
        )
        cls.user.groups.add(cls.staff_group)

    def setUp(self):
        self.client = Client(
            enforce_csrf_checks=True
        )

    def get_csrf_token(self):
        response = self.client.get(
            "/api/auth/csrf/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        cookie = self.client.cookies.get(
            "csrftoken"
        )

        self.assertIsNotNone(cookie)

        return cookie.value

    def login(self):
        token = self.get_csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            data={
                "username": self.user.username,
                "password": PASSWORD,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        return response

    def test_csrf_endpoint_is_public_and_issues_cookie(self):
        response = self.client.get(
            "/api/auth/csrf/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIn(
            "csrfToken",
            response.json(),
        )
        self.assertIn(
            "csrftoken",
            self.client.cookies,
        )

    def test_login_without_csrf_is_rejected(self):
        response = self.client.post(
            "/api/auth/login/",
            data={
                "username": self.user.username,
                "password": PASSWORD,
            },
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )
        self.assertTrue(
            response.get(
                "Content-Type",
                "",
            ).startswith("text/html")
        )
        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_login_missing_credentials_returns_400(self):
        token = self.get_csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            data={},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.json(),
            {
                "detail":
                    "Username and password are required."
            },
        )

    def test_invalid_credentials_return_401_without_challenge(self):
        token = self.get_csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            data={
                "username": self.user.username,
                "password": "WrongPassword123!",
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            response.json(),
            {
                "detail":
                    "Invalid username or password."
            },
        )
        self.assertIsNone(
            response.get(
                "WWW-Authenticate"
            )
        )
        self.assertNotIn(
            "sessionid",
            self.client.cookies,
        )

    def test_successful_login_creates_session_and_rotates_csrf(self):
        initial_token = self.get_csrf_token()

        response = self.client.post(
            "/api/auth/login/",
            data={
                "username": self.user.username,
                "password": PASSWORD,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=initial_token,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json()["message"],
            "Login successful.",
        )

        self.assertIn(
            "sessionid",
            self.client.cookies,
        )
        self.assertIn(
            "csrftoken",
            self.client.cookies,
        )

        current_token = (
            self.client.cookies[
                "csrftoken"
            ].value
        )

        self.assertNotEqual(
            initial_token,
            current_token,
        )

        session_cookie = (
            self.client.cookies[
                "sessionid"
            ]
        )

        self.assertTrue(
            bool(
                session_cookie[
                    "httponly"
                ]
            )
        )
        self.assertEqual(
            session_cookie[
                "samesite"
            ],
            "Lax",
        )
        self.assertEqual(
            session_cookie[
                "path"
            ],
            "/",
        )

    def test_me_requires_authentication(self):
        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )
        self.assertTrue(
            response.get(
                "Content-Type",
                "",
            ).startswith(
                "application/problem+json"
            )
        )

    def test_me_returns_authenticated_user(self):
        login_response = self.login()

        self.assertEqual(
            login_response.status_code,
            200,
        )

        response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["id"],
            self.user.id,
        )
        self.assertEqual(
            body["username"],
            self.user.username,
        )
        self.assertEqual(
            body["email"],
            self.user.email,
        )

    def test_logout_requires_authentication(self):
        response = self.client.post(
            "/api/auth/logout/",
            data={},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            401,
        )
        self.assertEqual(
            response.get(
                "WWW-Authenticate"
            ),
            "Session",
        )

    def test_authenticated_logout_without_csrf_is_rejected(self):
        login_response = self.login()

        self.assertEqual(
            login_response.status_code,
            200,
        )

        response = self.client.post(
            "/api/auth/logout/",
            data={},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        me_response = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            me_response.status_code,
            200,
        )

    def test_pre_login_csrf_token_is_stale_after_login(self):
        initial_token = self.get_csrf_token()

        login_response = self.client.post(
            "/api/auth/login/",
            data={
                "username": self.user.username,
                "password": PASSWORD,
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=initial_token,
        )

        self.assertEqual(
            login_response.status_code,
            200,
        )

        response = self.client.post(
            "/api/auth/logout/",
            data={},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=initial_token,
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            self.client.get(
                "/api/auth/me/"
            ).status_code,
            200,
        )

    def test_valid_logout_destroys_session(self):
        login_response = self.login()

        self.assertEqual(
            login_response.status_code,
            200,
        )

        current_token = (
            self.client.cookies[
                "csrftoken"
            ].value
        )

        response = self.client.post(
            "/api/auth/logout/",
            data={},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=current_token,
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.json(),
            {
                "message":
                    "Logout successful."
            },
        )

        deletion_cookie = (
            response.cookies.get(
                "sessionid"
            )
        )

        self.assertIsNotNone(
            deletion_cookie
        )
        self.assertTrue(
            deletion_cookie.value == ""
            or str(
                deletion_cookie[
                    "max-age"
                ]
            ) == "0"
        )

        after_logout = self.client.get(
            "/api/auth/me/"
        )

        self.assertEqual(
            after_logout.status_code,
            401,
        )
        self.assertEqual(
            after_logout.get(
                "WWW-Authenticate"
            ),
            "Session",
        )
