"""Production login throttle; shared cache required across web workers."""
from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle

class LoginThrottle(SimpleRateThrottle):
    scope='login'
    rate='10/min'
    def get_cache_key(self,request,view):
        return self.cache_format % {'scope':self.scope,'ident':self.get_ident(request)}
    def allow_request(self,request,view):
        if not settings.LOGIN_THROTTLE_ENABLED:return True
        return super().allow_request(request,view)
