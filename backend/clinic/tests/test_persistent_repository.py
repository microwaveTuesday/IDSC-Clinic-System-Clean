from django.test import TestCase
from django.db import IntegrityError,transaction
from clinic.data.persistent import PersistentClinicRepository
from clinic.models import HealthRecord, MedicineDispensation
from clinic.mutations import expected_etag,record_etag
from clinic.exceptions import ConflictError

class PersistentRepositoryTests(TestCase):
    def setUp(self):self.repo=PersistentClinicRepository()
    def test_crud_and_new_instance_reads_durable_rows(self):
        for kind,values in [('health_record',{'student_id':'external-1','blood_type':'O+'}),('consultation',{'student_id':'external-1','chief_complaint':'Headache'}),('health_status',{'student_id':'external-1','status':'CLEARED'})]:
            row=getattr(self.repo,'create_'+kind)(values)
            model=self.repo.models[kind];key=row[model._meta.pk.name]
            other=PersistentClinicRepository()
            self.assertEqual(getattr(other,'get_'+kind)(key),row)
            self.assertIsNotNone(getattr(other,'update_'+kind)(key,{'student_id':'external-2'}))
            getattr(other,'delete_'+kind)(key)
            self.assertIsNone(getattr(self.repo,'get_'+kind)(key))
    def test_dispensation_rollback_and_history_delete(self):
        row=self.repo.create_dispensation({'student_id':'s','medicine_id':'m','quantity':2},'external-tx')
        self.assertEqual(self.repo.rollback_dispensation(row['dispensation_id'],'external-restore')['status'],'ROLLED_BACK')
        self.repo.delete_dispensation(row['dispensation_id'])
        self.assertEqual(MedicineDispensation.objects.count(),0)
    def test_stale_update_and_delete_conflict(self):
        row=self.repo.create_health_record({'student_id':'s'})
        token=expected_etag.set(record_etag(row))
        try:
            self.repo.update_health_record(row['health_record_id'],{'allergies':'updated'})
            with self.assertRaises(ConflictError):self.repo.update_health_record(row['health_record_id'],{'allergies':'lost'})
            with self.assertRaises(ConflictError):self.repo.delete_health_record(row['health_record_id'])
        finally:expected_etag.reset(token)
    def test_quantity_constraint_and_transaction_reference_uniqueness(self):
        data={'student_id':'s','medicine_id':'m','quantity':1,'inventory_transaction_id':'tx'}
        MedicineDispensation.objects.create(**data)
        with self.assertRaises(IntegrityError),transaction.atomic():MedicineDispensation.objects.create(**data)
        with self.assertRaises(IntegrityError),transaction.atomic():MedicineDispensation.objects.create(student_id='s',medicine_id='m',quantity=0)
    def test_latest_status_and_missing_resource(self):
        self.repo.create_health_status({'student_id':'s','status':'CLEARED'})
        self.assertEqual(self.repo.get_latest_health_status_for_student('s')['status'],'CLEARED')
        self.assertIsNone(self.repo.get_health_record(999))
