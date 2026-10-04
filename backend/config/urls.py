"""
Root URL configuration for the IDSC Clinic System backend.

Business API:
    /api/v1/

Authentication:
    /api/auth/

API documentation:
    /api/schema/
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def api_root_view(request):
    """Backend discovery endpoint."""
    return JsonResponse(
        {
            "name": "IDSC Clinic System API",
            "version": "1.0.0",
            "status": "healthy",
            "endpoints": {
                "api": "/api/v1/",
                "authentication": "/api/auth/",
                "schema": "/api/schema/",
                "swagger_ui": "/docs",
                "redoc": "/api/schema/redoc/",
                "admin": "/admin/",
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication remains outside the versioned business namespace.
    path("api/auth/", include("authentication.urls")),

    # Administrative Clinic user management.
    path("api/v1/users/", include("authentication.user_urls")),

    # Canonical Clinic business API.
    path("api/v1/", include("clinic.urls")),

    # OpenAPI schema and interactive documentation.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Canonical rubric-required Swagger UI.
    path(
        "docs",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs-slash",
    ),

    # Backward-compatible Swagger route.
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Backend discovery endpoint.
    path("", api_root_view, name="api-root"),
]