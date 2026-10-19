"""Shared mutation coordination and conditional-write tokens."""
import hashlib
import json
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from clinic.models import MutationLock

process_lock = RLock()
expected_etag = ContextVar('expected_etag', default=None)
expected_version = ContextVar('expected_version', default=None)
pending_incidents = ContextVar('pending_incidents', default=None)

def record_etag(record):
    from datetime import datetime
    from django.utils.dateparse import parse_datetime
    def normalize(value):
        if isinstance(value,dict):return {key:normalize(item) for key,item in value.items()}
        if isinstance(value,list):return [normalize(item) for item in value]
        if isinstance(value,str) and 'T' in value:
            try: parsed=parse_datetime(value)
            except ValueError: parsed=None
            if parsed:value=parsed
        if isinstance(value,datetime):return value.isoformat(timespec='microseconds').replace('+00:00','Z')
        return value
    encoded=json.dumps(normalize(record),cls=DjangoJSONEncoder,sort_keys=True,separators=(',',':'))
    return '"'+hashlib.sha256(encoded.encode()).hexdigest()+'"'

@contextmanager
def mutation_lock():
    # RLock also covers mock stock and allows nested repository/service operations.
    with process_lock, transaction.atomic():
        changed=MutationLock.objects.filter(name='clinic').update(name='clinic')
        if not changed:MutationLock.objects.get_or_create(name='clinic')
        yield


from functools import wraps
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from clinic.models import OperationReceipt
from clinic.exceptions import ConflictError


def guarded(method):
    """Optional durable idempotency, actor/path scoped, after DRF authorization."""
    @wraps(method)
    def call(self, request, *args, **kwargs):
        key=request.headers.get('Idempotency-Key')
        if key and (len(key)>128 or not key.isascii()):
            raise ValidationError('Idempotency-Key must be ASCII and at most 128 characters.')
        scope=hashlib.sha256(f'{request.user.pk}:{request.method}:{request.path}'.encode()).hexdigest()
        fingerprint=hashlib.sha256(json.dumps(request.data,sort_keys=True,cls=DjangoJSONEncoder).encode()).hexdigest()
        version=request.headers.get('X-Record-Version')
        if version:
            from django.utils.dateparse import parse_datetime
            try: parsed=parse_datetime(version) if len(version)<=64 else None
            except ValueError: parsed=None
            if parsed is None:raise ValidationError('X-Record-Version must be an ISO datetime.')
        token=expected_etag.set(request.headers.get('If-Match'))
        version_token=expected_version.set(request.headers.get('X-Record-Version'))
        try:
            with mutation_lock():
                receipt=None
                if key:
                    receipt=OperationReceipt.objects.filter(scope=scope,key=key).first()
                    if receipt:
                        if receipt.fingerprint!=fingerprint:raise ConflictError('Idempotency key reused with a different request.')
                        response=Response(receipt.response,status=receipt.status_code)
                        response['Idempotency-Replayed']='true'
                        return response
                response=method(self,request,*args,**kwargs)
                if key and 200 <= response.status_code < 300:
                    OperationReceipt.objects.create(scope=scope,key=key,fingerprint=fingerprint,
                        response=json.loads(json.dumps(response.data,cls=DjangoJSONEncoder)),status_code=response.status_code)
                return response
        finally:
            expected_etag.reset(token)
            expected_version.reset(version_token)
    return call
