from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from rest_framework.test import APIClient

from clinic.models import HealthRecord

User = get_user_model()
PASSWORD = "LifecycleActor!47392"


class AccountLifecycleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_group, _ = Group.objects.get_or_create(name="CLINIC_ADMIN")
        staff_group, _ = Group.objects.get_or_create(name="CLINIC_STAFF")
        cls.root = User.objects.create_superuser(username="lifecycle_root", password=PASSWORD)
        cls.admin = User.objects.create_user(username="lifecycle_admin", password=PASSWORD)
        cls.admin.groups.add(admin_group)
        cls.target = User.objects.create_user(username="lifecycle_target", password=PASSWORD)
        cls.target.groups.add(admin_group)
        cls.staff = User.objects.create_user(username="lifecycle_staff", password=PASSWORD)
        cls.staff.groups.add(staff_group)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.root)
        self.token = self.client.get("/api/auth/csrf/").json()["csrfToken"]

    def action(self, role="admins", target=None, action="deactivate", password=PASSWORD):
        target = target or self.target
        path = f"/api/v1/{role}/{target.pk}/"
        if action == "delete":
            return self.client.delete(path, {"current_password": password}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)
        return self.client.post(path + action + "/", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)

    def active_admins(self):
        from authentication.account_lifecycle import administrator_query
        return User.objects.filter(administrator_query(), is_active=True).distinct().count()

    def test_admin_deactivation_blocks_login_and_revokes_session(self):
        other = Client()
        other.force_login(self.target)
        key = other.cookies["sessionid"].value
        response = self.action()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])
        self.assertFalse(Session.objects.filter(session_key=key).exists())
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)
        self.assertFalse(Client().login(username=self.target.username, password=PASSWORD))

    def test_admin_reactivation_requires_fresh_login_not_old_session(self):
        other = Client()
        other.force_login(self.target)
        self.assertEqual(self.action().status_code, 200)
        self.assertEqual(self.action(action="activate").status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)
        self.assertTrue(Client().login(username=self.target.username, password=PASSWORD))

    def test_admin_redundant_state_changes_return_conflict(self):
        self.assertEqual(self.action(action="activate").status_code, 409)
        self.assertEqual(self.action().status_code, 200)
        self.assertEqual(self.action().status_code, 409)

    def test_admin_delete_removes_account_and_sessions(self):
        other = Client()
        other.force_login(self.target)
        target_id = self.target.pk
        response = self.action(action="delete")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(User.objects.filter(pk=target_id).exists())
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)
        self.assertFalse(Client().login(username=self.target.username, password=PASSWORD))

    def test_staff_delete_removes_account(self):
        response = self.action(role="users", target=self.staff, action="delete")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=self.staff.pk).exists())

    def test_inactive_staff_can_be_deleted(self):
        self.assertEqual(self.action(role="users", target=self.staff).status_code, 200)
        self.assertEqual(self.action(role="users", target=self.staff, action="delete").status_code, 204)

    def test_inactive_admin_can_be_deleted(self):
        self.assertEqual(self.action().status_code, 200)
        self.assertEqual(self.action(action="delete").status_code, 204)

    def test_staff_reactivation_does_not_revive_old_session(self):
        other = Client()
        other.force_login(self.staff)
        self.assertEqual(self.action(role="users", target=self.staff).status_code, 200)
        self.assertEqual(self.action(role="users", target=self.staff, action="activate").status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 401)
        self.assertTrue(Client().login(username=self.staff.username, password=PASSWORD))

    def test_self_delete_and_deactivation_are_rejected(self):
        for action in ["deactivate", "delete"]:
            self.assertEqual(self.action(target=self.root, action=action).status_code, 409)
        self.assertTrue(User.objects.get(pk=self.root.pk).is_active)

    def test_last_active_admin_remains_available(self):
        User.objects.filter(pk__in=[self.admin.pk, self.target.pk]).update(is_active=False)
        self.assertEqual(self.active_admins(), 1)
        for action in ["deactivate", "delete"]:
            self.assertEqual(self.action(target=self.root, action=action).status_code, 409)
            self.assertEqual(self.active_admins(), 1)

    def test_staff_is_denied_all_lifecycle_operations(self):
        self.client.force_login(self.staff)
        for action in ["activate", "deactivate", "delete"]:
            self.assertEqual(self.action(action=action).status_code, 403)
        self.assertEqual(self.action(role="users", target=self.staff, action="delete").status_code, 403)

    def test_anonymous_requests_are_rejected(self):
        self.client.logout()
        self.assertEqual(self.action().status_code, 401)
        self.assertEqual(self.action(action="delete").status_code, 401)
        self.assertEqual(self.action(role="users", target=self.staff, action="delete").status_code, 401)

    def test_csrf_is_required_for_new_operations(self):
        for path, method in [
            (f"/api/v1/admins/{self.target.pk}/", "delete"),
            (f"/api/v1/admins/{self.target.pk}/deactivate/", "post"),
            (f"/api/v1/admins/{self.target.pk}/activate/", "post"),
            (f"/api/v1/users/{self.staff.pk}/", "delete"),
        ]:
            response = getattr(self.client, method)(path, {}, content_type="application/json")
            self.assertEqual(response.status_code, 403)

    def test_deletion_requires_correct_actor_password(self):
        for role, target in [("admins", self.target), ("users", self.staff)]:
            self.assertEqual(self.action(role, target, "delete", "WrongActorPassword!123").status_code, 400)
            self.assertTrue(User.objects.filter(pk=target.pk).exists())
            response = self.client.delete(f"/api/v1/{role}/{target.pk}/", {}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)
            self.assertEqual(response.status_code, 400)

    def test_wrong_role_and_unknown_targets_are_not_found(self):
        self.assertEqual(self.action(target=self.staff, action="delete").status_code, 404)
        self.assertEqual(self.action(role="users", target=self.target, action="delete").status_code, 404)
        response = self.client.delete("/api/v1/admins/999999/", {"current_password": PASSWORD}, content_type="application/json", HTTP_X_CSRFTOKEN=self.token)
        self.assertEqual(response.status_code, 404)

    def test_mixed_role_admin_cannot_use_staff_lifecycle_routes(self):
        self.target.groups.add(Group.objects.get(name="CLINIC_STAFF"))
        for action in ["delete", "deactivate", "activate"]:
            self.assertEqual(self.action(role="users", target=self.target, action=action).status_code, 404)
        self.assertTrue(User.objects.get(pk=self.target.pk).is_active)

    def test_clinic_admin_cannot_manage_system_admin(self):
        self.client.force_login(self.admin)
        for action in ["delete", "deactivate", "activate"]:
            self.assertEqual(self.action(target=self.root, action=action).status_code, 403)

    def test_second_owner_is_rejected(self):
        from django.core.exceptions import ValidationError
        self.target.is_superuser = True
        with self.assertRaises(ValidationError):
            self.target.save(update_fields=["is_superuser"])

    def test_directory_is_owner_only_and_excludes_owner(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/api/v1/admins/").status_code, 403)
        self.client.force_login(self.root)
        rows = {row["user_id"]: row for row in self.client.get("/api/v1/admins/").json()}
        self.assertNotIn(self.root.pk, rows)
        self.assertTrue(rows[self.admin.pk]["can_manage"])
        self.assertTrue(rows[self.target.pk]["can_manage"])

    def test_disabled_actor_is_rechecked_under_lock(self):
        User.objects.filter(pk=self.root.pk).update(is_active=False)
        forced = APIClient()
        forced.force_authenticate(user=self.root)
        self.assertEqual(forced.post(f"/api/v1/admins/{self.target.pk}/deactivate/").status_code, 403)

    def test_deactivation_preserves_unrelated_sessions(self):
        other = Client()
        other.force_login(self.staff)
        self.assertEqual(self.action().status_code, 200)
        self.assertEqual(other.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_deletion_preserves_clinic_medical_records(self):
        record = HealthRecord.objects.create(student_id="2026-0001")
        self.assertEqual(self.action(role="users", target=self.staff, action="delete").status_code, 204)
        self.assertTrue(HealthRecord.objects.filter(pk=record.pk).exists())

    def test_repeated_deletion_returns_not_found(self):
        self.assertEqual(self.action(action="delete").status_code, 204)
        self.assertEqual(self.action(action="delete").status_code, 404)
