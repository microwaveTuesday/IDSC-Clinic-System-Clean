from copy import deepcopy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, Client, override_settings
from rest_framework.test import APIClient
from clinic import demo_integrations as demo
from clinic.services.registrar import registrar_service
from clinic.services.inventory import inventory_service
from clinic.services.clinic import clinic_service

User = get_user_model()
PASSWORD = "ExternalWorkflow!49382"


class ExternalWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(username="external_owner",password=PASSWORD)
        cls.admin = User.objects.create_user(username="external_admin",password=PASSWORD)
        cls.admin.groups.add(Group.objects.get(name="CLINIC_ADMIN"))
        cls.staff = User.objects.create_user(username="external_staff",password=PASSWORD)
        cls.staff.groups.add(Group.objects.get(name="CLINIC_STAFF"))

    def setUp(self):
        self.saved_students = deepcopy(registrar_service._students)
        self.saved_inventory = deepcopy(inventory_service.__dict__)
        self.saved_restocks = deepcopy(demo.restocks)
        self.saved_notifications = deepcopy(demo.notifications)
        self.saved_reads = deepcopy(demo.read_notifications)
        self.saved_clinic = deepcopy(clinic_service.repository.__dict__)
        demo.restocks.clear();demo.notifications.clear();demo.read_notifications.clear()
        self.client = APIClient();self.client.force_authenticate(self.owner)

    def tearDown(self):
        registrar_service._students=self.saved_students
        inventory_service.__dict__.clear();inventory_service.__dict__.update(self.saved_inventory)
        demo.restocks.clear();demo.restocks.update(self.saved_restocks)
        demo.notifications[:]=self.saved_notifications
        demo.read_notifications.clear();demo.read_notifications.update(self.saved_reads)
        clinic_service.repository.__dict__.clear();clinic_service.repository.__dict__.update(self.saved_clinic)

    def post(self,path,data=None):
        return self.client.post('/api/v1/'+path,data or {},format='json')

    def new_student(self, status='ACTIVE'):
        return self.post('mock/registrar/students/',{'student_id':'TEST-123','first_name':'Original','last_name':'Student','course':'BSIT','section':'1A','status':status})

    def new_medicine(self, name='Test Medicine', medicine_id='MED-TEST'):
        return self.post('mock/inventory/medicines/',{'medicine_id':medicine_id,'name':name,'generic_name':'Test','unit':'tablet','quantity_in_stock':10,'reorder_level':5,'status':'ACTIVE'})

    def request_selected(self, medicine_id='MED-0001',quantity=7):
        return self.post('restock-requests/',{'mode':'SELECTED','items':[{'medicine_id':medicine_id,'quantity':quantity}]})

    def test_get_student_by_id_returns_registrar_profile_and_updates(self):
        self.assertEqual(self.new_student().status_code,201)
        response=self.post('students/import/',{'student_id':'TEST-123'})
        self.assertEqual(response.status_code,200);self.assertEqual(response.json()['first_name'],'Original')
        response=self.client.patch('/api/v1/mock/registrar/students/TEST-123/',{'first_name':'Updated','course':'BSCS'},format='json')
        self.assertEqual(response.status_code,200)
        response=self.client.get('/api/v1/students/TEST-123/')
        self.assertEqual(response.json()['first_name'],'Updated');self.assertEqual(response.json()['course'],'BSCS')
        self.assertEqual(self.post('students/import/',{'student_id':'MISSING'}).status_code,404)
        self.assertEqual(self.post('students/import/').status_code,400)

    def test_graduated_and_dropped_students_cannot_create_any_new_clinic_record(self):
        self.new_student()
        for state in ['GRADUATED','DROPPED_OUT']:
            self.client.patch('/api/v1/mock/registrar/students/TEST-123/',{'status':state},format='json')
            for path,data in [('health-records/',{'student_id':'TEST-123','blood_type':'O+'}),('consultations/',{'student_id':'TEST-123','chief_complaint':'Test'}),('health-statuses/',{'student_id':'TEST-123','status':'CLEARED','remarks':'Test'}),('medicine-dispensations/',{'student_id':'TEST-123','medicine_id':'MED-0001','quantity':1,'reason':'Test'})]:
                with self.subTest(state=state,path=path):self.assertEqual(self.post(path,data).status_code,422)
        self.client.patch('/api/v1/mock/registrar/students/TEST-123/',{'status':'ACTIVE'},format='json')
        self.assertEqual(self.post('health-records/',{'student_id':'TEST-123','blood_type':'O+'}).status_code,201)

    def test_mock_external_writes_and_fulfillment_are_owner_only(self):
        for actor in [self.admin,self.staff]:
            self.client.force_authenticate(actor)
            for method,path in [('get','mock/registrar/students/'),('post','mock/registrar/students/'),('patch','mock/registrar/students/2026-0001/'),('get','mock/inventory/medicines/'),('post','mock/inventory/medicines/'),('patch','mock/inventory/medicines/MED-0001/'),('delete','mock/inventory/medicines/MED-0001/'),('post','mock/inventory/restock-requests/missing/fulfill/')]:
                self.assertEqual(getattr(self.client,method)('/api/v1/'+path,{},format='json').status_code,403)
            self.assertEqual(self.post('students/import/',{'student_id':'2026-0001'}).status_code,200)
            self.assertEqual(self.request_selected().status_code,201)

    def test_student_ids_immutable_and_duplicate_rejected(self):
        self.new_student()
        self.assertEqual(self.new_student().status_code,409)
        self.assertEqual(self.client.patch('/api/v1/mock/registrar/students/TEST-123/',{'student_id':'NEW'},format='json').status_code,400)
        self.assertEqual(self.client.patch('/api/v1/mock/registrar/students/TEST-123/',{'status':'INVALID'},format='json').status_code,400)

    def test_inventory_catalog_live_notifications_edit_delete_and_per_user_receipts(self):
        self.assertEqual(self.new_medicine().status_code,201)
        self.assertEqual(self.client.get('/api/v1/medicines/MED-TEST/').json()['name'],'Test Medicine')
        notices=self.client.get('/api/v1/inventory-notifications/').json()
        self.assertEqual(notices[0]['kind'],'MEDICINE_ADDED')
        self.assertEqual(self.post('inventory-notifications/',{'notification_ids':[notices[0]['notification_id']]}).status_code,204)
        self.assertEqual(self.client.get('/api/v1/inventory-notifications/').json(),[])
        self.client.force_authenticate(self.staff)
        self.assertEqual(len(self.client.get('/api/v1/inventory-notifications/').json()),1)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch('/api/v1/mock/inventory/medicines/MED-TEST/',{'name':'Changed'},format='json').status_code,200)
        self.assertEqual(self.client.get('/api/v1/medicines/MED-TEST/').json()['name'],'Changed')
        self.assertEqual(self.client.delete('/api/v1/mock/inventory/medicines/MED-TEST/').status_code,204)
        self.assertEqual(self.client.get('/api/v1/medicines/MED-TEST/').status_code,404)

    def test_inventory_validation(self):
        self.new_medicine()
        self.assertEqual(self.new_medicine().status_code,409)
        self.assertEqual(self.client.patch('/api/v1/mock/inventory/medicines/MED-TEST/',{'quantity_in_stock':-1},format='json').status_code,400)
        self.assertEqual(self.client.patch('/api/v1/mock/inventory/medicines/MED-TEST/',{'medicine_id':'CHANGED'},format='json').status_code,400)

    def test_selected_restock_waits_for_inventory_and_cannot_double_fulfill(self):
        before=inventory_service.get_medicine('MED-0001')['quantity_in_stock']
        response=self.request_selected();self.assertEqual(response.status_code,201)
        request_id=response.json()['request_id']
        self.assertEqual(inventory_service.get_medicine('MED-0001')['quantity_in_stock'],before)
        self.assertEqual(self.post(f'mock/inventory/restock-requests/{request_id}/fulfill/').status_code,200)
        self.assertEqual(inventory_service.get_medicine('MED-0001')['quantity_in_stock'],before+7)
        self.assertEqual(self.post(f'mock/inventory/restock-requests/{request_id}/fulfill/').status_code,409)
        self.assertEqual(inventory_service.get_medicine('MED-0001')['quantity_in_stock'],before+7)

    def test_all_restock_delivers_to_every_active_medicine(self):
        before={m['medicine_id']:m['quantity_in_stock'] for m in inventory_service.list_medicines(status='ACTIVE')}
        response=self.post('restock-requests/',{'mode':'ALL','quantity':3});self.assertEqual(response.status_code,201)
        self.post('mock/inventory/restock-requests/'+response.json()['request_id']+'/fulfill/')
        for key,quantity in before.items():self.assertEqual(inventory_service.get_medicine(key)['quantity_in_stock'],quantity+3)

    def test_invalid_and_duplicate_items_rejected(self):
        self.assertEqual(self.post('restock-requests/',{'mode':'SELECTED','items':[]}).status_code,400)
        self.assertEqual(self.request_selected(quantity=0).status_code,400)
        self.assertEqual(self.request_selected(medicine_id='MISSING').status_code,404)
        item={'medicine_id':'MED-0001','quantity':1}
        self.assertEqual(self.post('restock-requests/',{'mode':'SELECTED','items':[item,item]}).status_code,400)

    def test_fulfillment_validates_whole_delivery_before_stock_changes(self):
        response=self.post('restock-requests/',{'mode':'ALL','quantity':2})
        before=inventory_service.get_medicine('MED-0001')['quantity_in_stock']
        self.client.patch('/api/v1/mock/inventory/medicines/MED-0002/',{'status':'INACTIVE'},format='json')
        self.assertEqual(self.post('mock/inventory/restock-requests/'+response.json()['request_id']+'/fulfill/').status_code,409)
        self.assertEqual(inventory_service.get_medicine('MED-0001')['quantity_in_stock'],before)
        self.assertEqual(self.client.get('/api/v1/restock-requests/').json()[0]['status'],'PENDING')

    def test_pending_requests_and_stock_transactions_protect_catalog(self):
        self.new_medicine();self.request_selected('MED-TEST')
        self.assertEqual(self.client.delete('/api/v1/mock/inventory/medicines/MED-TEST/').status_code,409)
        row=self.client.get('/api/v1/restock-requests/').json()[0]
        self.post('mock/inventory/restock-requests/'+row['request_id']+'/fulfill/')
        self.assertEqual(self.client.delete('/api/v1/mock/inventory/medicines/MED-TEST/').status_code,409)

    def test_only_owner_and_admin_can_delete_clinical_records(self):
        for resource,create,key in [('health-records',clinic_service.repository.create_health_record,'health_record_id'),('consultations',clinic_service.repository.create_consultation,'consultation_id'),('health-statuses',clinic_service.repository.create_health_status,'status_id')]:
            for actor in [self.owner,self.admin,self.staff]:
                record=create({'student_id':'2026-0001','blood_type':'O+','chief_complaint':'Test','status':'CLEARED'})
                self.client.force_authenticate(actor)
                response=self.client.delete(f'/api/v1/{resource}/{record[key]}/')
                self.assertEqual(response.status_code,403 if actor==self.staff else 204)

    def test_deleting_history_does_not_return_stock_or_remove_inventory_transaction(self):
        for actor in [self.owner,self.admin,self.staff]:
            self.client.force_authenticate(actor)
            response=self.post('medicine-dispensations/',{'student_id':'2026-0001','medicine_id':'MED-0001','quantity':1,'reason':'Test'})
            self.assertEqual(response.status_code,201)
            row=response.json();before=inventory_service.get_medicine('MED-0001')['quantity_in_stock']
            self.assertEqual(self.client.delete(f"/api/v1/medicine-dispensations/{row['dispensation_id']}/").status_code,403 if actor==self.staff else 204)
            self.assertEqual(inventory_service.get_medicine('MED-0001')['quantity_in_stock'],before)
            self.assertIn(row['inventory_transaction_id'],inventory_service._transactions)

    def test_session_authentication_and_csrf_on_new_endpoints(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.post('students/import/',{'student_id':'2026-0001'}).status_code,401)
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        for path in ['students/import/','mock/registrar/students/','mock/inventory/medicines/','restock-requests/','inventory-notifications/']:
            self.assertEqual(client.post('/api/v1/'+path,{},content_type='application/json').status_code,403)

    @override_settings(MOCK_WORKSPACES_ENABLED=False)
    def test_demo_routes_can_be_explicitly_disabled(self):
        self.assertEqual(self.client.get('/api/v1/mock/registrar/students/').status_code,404)
