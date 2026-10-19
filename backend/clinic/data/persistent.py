"""ORM repository. External identities and stock remain opaque references."""
from django.db import transaction
from django.utils import timezone
from clinic.models import HealthRecord, Consultation, HealthStatus, MedicineDispensation
from clinic.exceptions import ConflictError
from clinic.mutations import expected_etag, expected_version, record_etag, mutation_lock


class PersistentClinicRepository:
    models = {'health_record': HealthRecord, 'consultation': Consultation,
              'health_status': HealthStatus, 'dispensation': MedicineDispensation}

    @staticmethod
    def serialize(instance):
        return {field.attname: getattr(instance, field.attname) for field in instance._meta.concrete_fields}

    def list(self, kind):
        return list(self.models[kind].objects.values())

    def get(self, kind, key):
        row = self.models[kind].objects.filter(pk=key).first()
        return self.serialize(row) if row else None

    def create(self, kind, values):
        model = self.models[kind]
        allowed = {f.name for f in model._meta.fields if f.editable and not f.primary_key}
        with transaction.atomic():
            row = model(**{k:v for k,v in values.items() if k in allowed})
            row.full_clean()
            row.save()
            return self.serialize(row)

    def update(self, kind, key, values):
        with mutation_lock():
            row = self.models[kind].objects.select_for_update().filter(pk=key).first()
            if not row:
                return None
            from django.utils.dateparse import parse_datetime
            if expected_version.get() and parse_datetime(expected_version.get()) != getattr(row,'updated_at',None):
                raise ConflictError('This record changed. Reload before saving your edits.')
            snapshot = self.serialize(row)
            if expected_etag.get() and expected_etag.get() != record_etag(snapshot):
                raise ConflictError('This record changed. Reload before saving your edits.')
            allowed = {f.name for f in row._meta.fields if f.editable and not f.primary_key}
            for name,value in values.items():
                if name in allowed:
                    setattr(row,name,value)
            row.full_clean()
            row.save()
            return self.serialize(row)

    def delete(self, kind, key):
        with mutation_lock():
            row = self.models[kind].objects.select_for_update().filter(pk=key).first()
            if not row:return None
            data = self.serialize(row)
            if expected_etag.get() and expected_etag.get() != record_etag(data):
                raise ConflictError('This record changed. Reload before deleting.')
            row.delete()
            return data

    def create_dispensation(self, values, inventory_transaction_id):
        return self.create('dispensation', {**values, 'inventory_transaction_id': inventory_transaction_id})

    def rollback_dispensation(self, key, rollback_transaction_id):
        with mutation_lock():
            row = MedicineDispensation.objects.select_for_update().filter(pk=key).first()
            if not row:return None
            if row.status == 'ROLLED_BACK':raise ConflictError('Already rolled back.')
            row.status='ROLLED_BACK'; row.rollback_transaction_id=rollback_transaction_id
            row.rolled_back_at=timezone.now();row.save()
            return self.serialize(row)

    def get_latest_health_status_for_student(self, student_id):
        row=HealthStatus.objects.filter(student_id=student_id).first()
        return self.serialize(row) if row else None


# Bind the established repository protocol without duplicating identical ORM CRUD.
def bind(kind, verb):
    return lambda self,*args: getattr(self,verb)(kind,*args)
for kind, plural in [('health_record','health_records'),('consultation','consultations'),('health_status','health_statuses'),('dispensation','dispensations')]:
    setattr(PersistentClinicRepository,'list_'+plural,bind(kind,'list'))
    setattr(PersistentClinicRepository,'get_'+kind,bind(kind,'get'))
    setattr(PersistentClinicRepository,'delete_'+kind,bind(kind,'delete'))
    if kind != 'dispensation':
        setattr(PersistentClinicRepository,'create_'+kind,bind(kind,'create'))
        setattr(PersistentClinicRepository,'update_'+kind,bind(kind,'update'))
