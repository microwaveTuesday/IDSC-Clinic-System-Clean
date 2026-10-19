"""Metadata audit and sensitive-response cache protection."""
from clinic.models import AuditEvent,IntegrationIncident
from clinic.mutations import record_etag,pending_incidents


class ClinicResponseMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        incidents=[]
        token=pending_incidents.set(incidents)
        try:response=self.get_response(request)
        finally:pending_incidents.reset(token)
        for incident in incidents:IntegrationIncident.objects.create(**incident)
        if request.path.startswith('/api/'):
            response['Cache-Control']='no-store'
            data=getattr(response,'data',None)
            if isinstance(data,dict) and ('updated_at' in data or 'dispensation_id' in data):
                response['ETag']=record_etag(data)
            if request.method not in ('GET','HEAD','OPTIONS'):
                # No query strings, credentials, bodies, student IDs or medical values.
                path=str(getattr(request.resolver_match,'route','/unmatched/'))
                AuditEvent.objects.create(actor_id=str(getattr(request.user,'pk','') or ''),method=request.method,
                    path=path[:256],status_code=response.status_code)
        return response
