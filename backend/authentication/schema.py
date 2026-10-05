"""
OpenAPI schema extensions for Clinic authentication.

Runtime authentication remains ClinicSessionAuthentication.
This module only teaches drf-spectacular how that authentication
mechanism should appear in generated OpenAPI documents.
"""

from django.conf import settings
from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension,
)


class ClinicSessionAuthenticationScheme(
    OpenApiAuthenticationExtension
):
    """
    Describe ClinicSessionAuthentication as Django session-cookie auth.
    """

    target_class = (
        "authentication.authentication."
        "ClinicSessionAuthentication"
    )

    # Match drf-spectacular's conventional SessionAuthentication name.
    name = "cookieAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": settings.SESSION_COOKIE_NAME,
            "description": (
                "Django session cookie authentication. "
                "State-changing session-authenticated requests "
                "must also satisfy Django CSRF protection."
            ),
        }
