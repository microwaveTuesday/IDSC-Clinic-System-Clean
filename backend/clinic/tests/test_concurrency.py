from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.test import TransactionTestCase,Client
from django.db import connection,connections
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from clinic.models import MutationLock,OperationReceipt
from clinic.services.clinic import clinic_service

@skipUnless(connection.vendor=='postgresql','Real row-lock concurrency is verified against PostgreSQL.')
class ConcurrentWritesTests(TransactionTestCase):
    def setUp(self):
        MutationLock.objects.get_or_create(name='clinic')
        clinic_service.clear_mock_data()
    def test_simultaneous_owner_registration_has_one_winner(self):
        gate=Barrier(2)
        def register(i):
            c=Client(enforce_csrf_checks=True)
            token=c.get('/api/auth/csrf/').json()['csrfToken'];gate.wait()
            r=c.post('/api/auth/owner/register/',{'username':f'owner_{i}','password':'WinterGarden!49183','confirm_password':'WinterGarden!49183'},content_type='application/json',HTTP_X_CSRFTOKEN=token)
            connections.close_all();return r.status_code
        with ThreadPoolExecutor(2) as pool:statuses=list(pool.map(register,[1,2]))
        self.assertEqual(sorted(statuses),[201,409]);self.assertEqual(get_user_model().objects.filter(is_superuser=True).count(),1)
    def test_parallel_same_request_has_one_receipt_and_record(self):
        user=get_user_model().objects.create_user(username='parallel')
        group,_=Group.objects.get_or_create(name='CLINIC_STAFF');user.groups.add(group)
        gate=Barrier(2)
        def create(_):
            c=Client();c.force_login(user);gate.wait()
            r=c.post('/api/v1/health-records/',{'student_id':'2026-0001','blood_type':'O+'},content_type='application/json',HTTP_IDEMPOTENCY_KEY='parallel-one')
            connections.close_all();return r.status_code
        with ThreadPoolExecutor(2) as pool:statuses=list(pool.map(create,[1,2]))
        self.assertEqual(statuses,[201,201]);self.assertEqual(OperationReceipt.objects.count(),1)
        self.assertEqual(clinic_service.total_health_records(),1)
