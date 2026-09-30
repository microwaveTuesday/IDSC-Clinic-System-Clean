"""
Canonical URL configuration for the Clinic business API.

This module is mounted by config.urls at:

    /api/v1/
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ConsultationViewSet,
    HealthRecordViewSet,
    HealthStatusIntegrationView,
    HealthStatusViewSet,
    HealthView,
    MedicineDetailView,
    MedicineDispensationViewSet,
    MedicineListView,
    StudentDetailView,
    StudentListView,
)


router = DefaultRouter()

router.register(
    r"health-records",
    HealthRecordViewSet,
    basename="health-record",
)

router.register(
    r"consultations",
    ConsultationViewSet,
    basename="consultation",
)

router.register(
    r"health-statuses",
    HealthStatusViewSet,
    basename="health-status",
)

router.register(
    r"medicine-dispensations",
    MedicineDispensationViewSet,
    basename="medicine-dispensation",
)


urlpatterns = [
    path(
        "health/",
        HealthView.as_view(),
        name="health",
    ),

    # Registrar-backed read-only student projection.
    path(
        "students/",
        StudentListView.as_view(),
        name="student-list",
    ),
    path(
        "students/<str:student_id>/",
        StudentDetailView.as_view(),
        name="student-detail",
    ),

    # Inventory-backed read-only medicine projection.
    path(
        "medicines/",
        MedicineListView.as_view(),
        name="medicine-list",
    ),
    path(
        "medicines/<str:medicine_id>/",
        MedicineDetailView.as_view(),
        name="medicine-detail",
    ),

    # Read-only integration projections.
    path(
        "integrations/faculty/health-status/<str:student_id>/",
        HealthStatusIntegrationView.as_view(),
        name="faculty-health-status",
    ),
    path(
        "integrations/student-portal/health-status/<str:student_id>/",
        HealthStatusIntegrationView.as_view(),
        name="student-portal-health-status",
    ),
]

urlpatterns += router.urls