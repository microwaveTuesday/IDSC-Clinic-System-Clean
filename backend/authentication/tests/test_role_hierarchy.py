from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase

User = get_user_model()
PASSWORD = "HierarchyAccount!58479"


class RoleHierarchyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(username="hierarchy_owner", password=PASSWORD)
        cls.admin = User.objects.create_user(username="hierarchy_admin", password=PASSWORD)
        cls.admin.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        cls.staff = User.objects.create_user(username="hierarchy_staff", password=PASSWORD)
        cls.staff.groups.add(Group.objects.get(name="CLINIC_STAFF"))
        cls.admin2 = User.objects.create_user(username="hierarchy_admin2", password=PASSWORD)
        cls.admin2.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        cls.staff2 = User.objects.create_user(username="hierarchy_staff2", password=PASSWORD)
        cls.staff2.groups.add(Group.objects.get(name="CLINIC_STAFF"))

    def client_for(self, user):
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        token = client.get("/api/auth/csrf/").json()["csrfToken"]
        return client, {"content_type": "application/json", "HTTP_X_CSRFTOKEN": token}

    def test_session_and_login_expose_three_roles(self):
        for user, role in [(self.owner, "OWNER"), (self.admin, "ADMIN"), (self.staff, "STAFF")]:
            with self.subTest(role=role):
                client, headers = self.client_for(user)
                self.assertEqual(client.get("/api/auth/me/").json()["role"], role)
                response = client.post("/api/auth/login/", {"username": user.username, "password": PASSWORD}, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["user"]["role"], role)

    def test_all_roles_have_clinic_access(self):
        for user in [self.owner, self.admin, self.staff]:
            client, _ = self.client_for(user)
            for path in ["dashboard/", "students/", "medicines/", "health-records/", "consultations/", "health-statuses/", "medicine-dispensations/", "reports/clinic-visits/"]:
                with self.subTest(user=user.username, path=path):
                    self.assertEqual(client.get("/api/v1/" + path).status_code, 200)

    def test_admin_and_staff_denied_every_admin_operation(self):
        for actor in [self.admin, self.staff]:
            client, headers = self.client_for(actor)
            for method, path, data in [
                ("get", "admins/", {}), ("post", "admins/", {}),
                ("get", f"admins/{self.admin2.pk}/", {}),
                ("patch", f"admins/{self.admin2.pk}/", {"first_name": "Forbidden"}),
                ("put", f"admins/{self.admin2.pk}/", {"first_name": "Forbidden"}),
                ("delete", f"admins/{self.admin2.pk}/", {"current_password": PASSWORD}),
                ("post", f"admins/{self.admin2.pk}/activate/", {}),
                ("post", f"admins/{self.admin2.pk}/deactivate/", {}),
            ]:
                with self.subTest(actor=actor.username, method=method, path=path):
                    self.assertEqual(getattr(client, method)("/api/v1/" + path, data, **headers).status_code, 403)
        self.admin2.refresh_from_db()
        self.assertEqual(self.admin2.first_name, "")
        self.assertTrue(self.admin2.is_active)

    def test_owner_and_admin_manage_staff_complete_lifecycle(self):
        for actor in [self.owner, self.admin]:
            client, headers = self.client_for(actor)
            response = client.post("/api/v1/users/", {"username": "created_by_" + actor.username, "password": PASSWORD}, **headers)
            self.assertEqual(response.status_code, 201)
            user_id = response.json()["user_id"]
            path = f"/api/v1/users/{user_id}/"
            self.assertEqual(client.patch(path, {"username": "edited_by_" + actor.username, "first_name": "Edited"}, **headers).status_code, 200)
            self.assertEqual(client.post(path + "deactivate/", {}, **headers).status_code, 200)
            self.assertEqual(client.post(path + "activate/", {}, **headers).status_code, 200)
            self.assertEqual(client.delete(path, {"current_password": PASSWORD}, **headers).status_code, 204)
            self.assertFalse(User.objects.filter(pk=user_id).exists())

    def test_owner_can_edit_admin_username_and_profile(self):
        client, headers = self.client_for(self.owner)
        path = f"/api/v1/admins/{self.admin.pk}/"
        self.assertEqual(client.get(path).status_code, 200)
        self.assertEqual(client.patch(path, {"username": "owner_renamed_admin", "first_name": "Edited", "email": "changed@example.test"}, **headers).status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.username, "owner_renamed_admin")
        self.assertTrue(self.admin.check_password(PASSWORD))
        self.assertFalse(self.admin.is_superuser)
        self.assertEqual(client.put(path, {"first_name": "Full", "last_name": "Update", "email": "full@example.test"}, **headers).status_code, 200)

    def test_staff_denied_every_staff_management_operation(self):
        client, headers = self.client_for(self.staff)
        path = f"/api/v1/users/{self.staff2.pk}/"
        for method, url in [("get", "/api/v1/users/"), ("post", "/api/v1/users/"), ("get", path), ("put", path), ("patch", path), ("delete", path), ("post", path + "activate/"), ("post", path + "deactivate/")]:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(client, method)(url, {}, **headers).status_code, 403)

    def test_owner_protected_from_management_routes(self):
        for actor in [self.owner, self.admin]:
            client, headers = self.client_for(actor)
            for resource in ["admins", "users"]:
                path = f"/api/v1/{resource}/{self.owner.pk}/"
                for method, url in [("patch", path), ("delete", path), ("post", path + "activate/"), ("post", path + "deactivate/")]:
                    response = getattr(client, method)(url, {"current_password": PASSWORD}, **headers)
                    self.assertIn(response.status_code, [403, 404, 409])
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)
        self.assertTrue(self.owner.is_superuser)

    def test_owner_can_change_own_credentials_and_keep_session(self):
        client, headers = self.client_for(self.owner)
        response = client.post("/api/auth/username/change/", {"new_username": "renamed_owner", "current_password": PASSWORD}, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "OWNER")
        response = client.post("/api/auth/password/change/", {"current_password": PASSWORD, "new_password": "ChangedOwner!39285", "confirm_password": "ChangedOwner!39285"}, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get("/api/auth/me/").json()["role"], "OWNER")
        self.assertTrue(Client().login(username="renamed_owner", password="ChangedOwner!39285"))

    def test_mixed_role_accounts_cannot_bypass_hierarchy(self):
        self.admin2.groups.add(Group.objects.get(name="CLINIC_STAFF"))
        self.owner.groups.add(Group.objects.get(name="CLINIC_STAFF"), Group.objects.get(name="CLINIC_ADMIN"))
        for actor in [self.owner, self.admin]:
            client, headers = self.client_for(actor)
            listing = client.get("/api/v1/users/").json()
            rows = listing.get("results", []) if isinstance(listing, dict) else listing
            self.assertNotIn(self.admin2.pk, [row["user_id"] for row in rows])
            self.assertNotIn(self.owner.pk, [row["user_id"] for row in rows])
            for target in [self.admin2, self.owner]:
                path = f"/api/v1/users/{target.pk}/"
                for method in ["get", "put", "patch", "delete"]:
                    self.assertEqual(getattr(client, method)(path, {"first_name": "Bypass", "current_password": PASSWORD}, **headers).status_code, 404)

    def test_account_edit_rejects_privilege_and_access_fields(self):
        for actor, resource, target in [(self.owner, "admins", self.admin2), (self.admin, "users", self.staff2)]:
            client, headers = self.client_for(actor)
            for field, value in [("is_superuser", True), ("is_staff", True), ("role", "OWNER"), ("groups", []), ("is_active", False), ("password", "Injected!12")]:
                response = client.patch(f"/api/v1/{resource}/{target.pk}/", {field: value}, **headers)
                self.assertEqual(response.status_code, 400)
            target.refresh_from_db()
            self.assertFalse(target.is_superuser)
            self.assertTrue(target.is_active)
            self.assertTrue(target.check_password(PASSWORD))

    def test_account_edits_validate_duplicate_username_and_csrf(self):
        client, headers = self.client_for(self.owner)
        path = f"/api/v1/admins/{self.admin.pk}/"
        self.assertEqual(client.patch(path, {"username": self.staff.username.upper()}, **headers).status_code, 400)
        self.assertEqual(client.patch(path, {"username": "invalid name!"}, **headers).status_code, 400)
        self.assertEqual(client.patch(path, {"first_name": "No CSRF"}, content_type="application/json").status_code, 403)

    def test_owner_can_remove_last_regular_admin_without_losing_owner(self):
        client, headers = self.client_for(self.owner)
        User.objects.filter(pk=self.admin2.pk).delete()
        self.assertEqual(client.delete(f"/api/v1/admins/{self.admin.pk}/", {"current_password": PASSWORD}, **headers).status_code, 204)
        self.assertEqual(client.get("/api/auth/me/").json()["role"], "OWNER")
        self.assertEqual(client.get("/api/v1/users/").status_code, 200)
