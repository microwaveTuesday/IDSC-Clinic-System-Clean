from rest_framework.authentication import SessionAuthentication


class ClinicSessionAuthentication(SessionAuthentication):
    """
    Django session authentication for the Clinic API.

    Returning an authenticate header allows DRF to distinguish an
    unauthenticated request (401) from an authenticated request that lacks
    permission (403).
    """

    def authenticate_header(self, request):
        return "Session"
