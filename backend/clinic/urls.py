"""
Canonical URL configuration for the Clinic business API.

This module is mounted by config.urls at:

    /api/v1/
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    StudentPortalHealthStatusIntegrationView,
    FacultyHealthStatusIntegrationView,
    MedicineDispensationReportView,
    HealthStatusIntegrationView,
    MedicineInventoryReportView,
    MedicineDispensationViewSet,
    HealthRecordsReportView,
    ClinicVisitsReportView,
    HealthRecordViewSet,
    HealthStatusViewSet,
    ConsultationViewSet,
    MedicineDetailView,
    StudentDetailView,
    MedicineListView,
    StudentListView,
    DashboardView,
    HealthView,

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
    # Canonical rubric-compliant health endpoint.
    path(
        "health",
        HealthView.as_view(),
        name="health",
    ),

    # Backward-compatible trailing-slash runtime alias.
    #
    # The canonical OpenAPI path is /api/v1/health.
    # schema=None keeps this compatibility route functional
    # without duplicating the canonical operation in OpenAPI.
    path(
        "health/",
        HealthView.as_view(schema=None),
        name="health-slash",
    ),

    # Read-only integration projections.
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),

    # Read-only report endpoints.
    path(
        "reports/clinic-visits/",
        ClinicVisitsReportView.as_view(),
        name="clinic-visits-report",
    ),
    path(
        "reports/health-records/",
        HealthRecordsReportView.as_view(),
        name="health-records-report",
    ),
    path(
        "reports/medicine-inventory/",
        MedicineInventoryReportView.as_view(),
        name="medicine-inventory-report",
    ),
        path(
        "reports/medicine-dispensations/",
        MedicineDispensationReportView.as_view(),
        name="medicine-dispensations-report",
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
        FacultyHealthStatusIntegrationView.as_view(),
        name="faculty-health-status",
    ),
    path(
        "integrations/student-portal/health-status/<str:student_id>/",
        StudentPortalHealthStatusIntegrationView.as_view(),
        name="student-portal-health-status",
    ),
]

urlpatterns += router.urls