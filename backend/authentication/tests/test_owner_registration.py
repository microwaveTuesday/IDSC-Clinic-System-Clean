from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase

from authentication.models import OwnerRegistration

User = get_user_model()
PASSWORD = 'WinterGarden!49183'
URL = '/api/auth/owner/register/'
STATUS = '/api/auth/setup/'


class OwnerRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def token(self):
        return self.client.get('/api/auth/csrf/').json()['csrfToken']

    def register(self, **overrides):
        data = {'username': 'first_owner', 'password': PASSWORD, 'confirm_password': PASSWORD, 'email': 'owner@example.test'}
        data.update(overrides)
        return self.client.post(URL, data, content_type='application/json', HTTP_X_CSRFTOKEN=self.token())

    def test_fresh_install_status_is_public_boolean_and_not_cached(self):
        response = self.client.get(STATUS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'owner_registration_available': True})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_registration_creates_one_owner_and_starts_session(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['role'], 'OWNER')
        self.assertNotIn('password', response.json()['user'])
        owner = User.objects.get(username='first_owner')
        self.assertTrue(owner.is_superuser and owner.is_staff and owner.is_active)
        self.assertTrue(owner.check_password(PASSWORD))
        self.assertEqual(OwnerRegistration.objects.get(pk=1).owner_id, owner.pk)
        self.assertEqual(self.client.get('/api/auth/me/').json()['role'], 'OWNER')
        self.assertEqual(self.client.get('/api/v1/admins/').status_code, 200)
        self.assertFalse(self.client.get(STATUS).json()['owner_registration_available'])

    def test_logout_returns_login_and_registration_stays_closed(self):
        self.register()
        self.client.post('/api/auth/logout/', {}, content_type='application/json', HTTP_X_CSRFTOKEN=self.token())
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.assertFalse(self.client.get(STATUS).json()['owner_registration_available'])
        self.assertEqual(self.register(username='second_owner').status_code, 409)
        self.assertEqual(User.objects.filter(is_superuser=True).count(), 1)

    def test_existing_cli_owner_also_closes_registration(self):
        owner = User.objects.create_superuser(username='cli_owner',password=PASSWORD)
        self.assertEqual(OwnerRegistration.objects.get(pk=1).owner_id, owner.pk)
        self.assertFalse(self.client.get(STATUS).json()['owner_registration_available'])
        self.assertEqual(self.register().status_code, 409)

    def test_inactive_owner_does_not_reopen_setup(self):
        self.register()
        User.objects.filter(is_superuser=True).update(is_active=False)
        self.client.logout()
        self.assertFalse(self.client.get(STATUS).json()['owner_registration_available'])
        self.assertEqual(self.register(username='takeover').status_code, 409)

    def test_completed_latch_stays_closed_even_if_owner_flag_is_changed_outside_app(self):
        self.register()
        User.objects.filter(is_superuser=True).update(is_superuser=False)
        self.client.logout()
        self.assertFalse(self.client.get(STATUS).json()['owner_registration_available'])
        self.assertEqual(self.register(username='takeover').status_code, 409)

    def test_csrf_required_before_first_registration(self):
        self.assertEqual(self.client.post(URL, {}, content_type='application/json').status_code, 403)
        self.assertEqual(User.objects.filter(is_superuser=True).count(), 0)
        self.assertTrue(self.client.get(STATUS).json()['owner_registration_available'])

    def test_mismatched_and_weak_passwords_do_not_claim_setup(self):
        self.assertEqual(self.register(confirm_password='Different!49183').status_code, 400)
        for password in ['short', 'password', '1234567890']:
            self.assertEqual(self.register(password=password,confirm_password=password).status_code, 400)
        self.assertTrue(self.client.get(STATUS).json()['owner_registration_available'])
        self.assertIsNone(OwnerRegistration.objects.get(pk=1).owner_id)

    def test_username_validation_and_existing_staff_collision(self):
        User.objects.create_user(username='existing_staff')
        for name in ['', 'invalid name!', 'EXISTING_STAFF', 'x'*151]:
            self.assertEqual(self.register(username=name).status_code, 400)
        self.assertEqual(self.register(username='  normalized_owner  ').status_code, 201)
        self.assertTrue(User.objects.filter(username='normalized_owner').exists())

    def test_invalid_email_rejected(self):
        self.assertEqual(self.register(email='not-an-email').status_code, 400)
        self.assertTrue(self.client.get(STATUS).json()['owner_registration_available'])

    def test_request_cannot_change_the_registered_role(self):
        response = self.register(role='STAFF',is_superuser=False,is_staff=False,is_active=False,groups=['CLINIC_STAFF'])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['user']['role'], 'OWNER')
        self.assertFalse(User.objects.get(username='first_owner').groups.exists())

    def test_second_owner_blocked_by_regular_model_save(self):
        self.register()
        with self.assertRaises(ValidationError):
            User.objects.create_superuser(username='second_cli_owner',password=PASSWORD)
        self.assertFalse(User.objects.filter(username='second_cli_owner').exists())

    def test_database_unique_index_blocks_bulk_second_owner(self):
        self.register()
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(username='bypass_owner',is_superuser=True,is_staff=True)])
        self.assertEqual(User.objects.filter(is_superuser=True).count(), 1)

    def test_registered_owner_cannot_be_deleted_deactivated_or_demoted(self):
        self.register()
        owner = User.objects.get(username='first_owner')
        with self.assertRaises(ProtectedError):
            owner.delete()
        owner.is_active = False
        with self.assertRaises(ValidationError):owner.save()
        owner.is_active = True;owner.is_superuser = False
        with self.assertRaises(ValidationError):owner.save()

    def test_only_one_registration_row_is_allowed(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OwnerRegistration.objects.create(pk=2)

    def test_other_anonymous_browser_and_authenticated_owner_cannot_register_again(self):
        self.register()
        other = Client(enforce_csrf_checks=True)
        token = other.get('/api/auth/csrf/').json()['csrfToken']
        self.assertEqual(other.post(URL,{},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code, 409)
        self.assertEqual(self.register(username='another').status_code, 409)
