"""
Canonical API controllers for the IDSC Clinic System.

Clinic owns:
- HealthRecord
- Consultation
- HealthStatus
- MedicineDispensation

Registrar owns student identity/profile data.
Inventory owns medicine catalog and stock data.

External data is accessed through service boundaries rather than local
Clinic ORM models.
"""

from authentication.permissions import IsClinicStaff, IsClinicAdmin
from clinic.mutations import guarded

from .pagination import ClinicPagination


from django.utils.dateparse import parse_date

from rest_framework.exceptions import (
    APIException,
    NotFound,
    ValidationError,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)

from .serializers import (
    ClinicVisitsReportSerializer,
    ConsultationSerializer,
    DashboardSerializer,
    HealthCheckSerializer,
    HealthRecordSerializer,
    HealthRecordsReportSerializer,
    HealthStatusProjectionSerializer,
    HealthStatusSerializer,
    MedicineDispensationReportSerializer,
    MedicineDispensationSerializer,
    MedicineInventoryReportSerializer,
    MedicineSerializer,
    PaginatedMedicineSerializer,
    PaginatedStudentSerializer,
    StudentSerializer,
)
from .services.clinic import (
    ClinicDispensationAlreadyRolledBackError,
    ClinicDispensationRollbackUnavailableError,
    ClinicResourceNotFoundError,
    clinic_service,
)
from .services.inventory import (
    InsufficientStockError,
    InventoryTransactionNotFoundError,
    MedicineNotFoundError,
    MedicineUnavailableError,
    inventory_service,
)
from .services.registrar import (
    StudentNotFoundError,
    StudentUnavailableError,
    registrar_service,
)

# ---------------------------------------------------------------------------
# OpenAPI schema helpers
# ---------------------------------------------------------------------------


def _int64_path_schema(
    parameter_name,
    description,
):
    """
    Build a method-level OpenAPI override for a Clinic-owned
    BigAutoField resource identifier.

    This changes schema metadata only. Runtime routing is unchanged.
    """
    return extend_schema(
        parameters=[
            OpenApiParameter(
                name=parameter_name,
                type=OpenApiTypes.INT64,
                location=OpenApiParameter.PATH,
                required=True,
                description=description,
            )
        ]
    )


# HTTP 422 exception for business-rule failures handled by the canonical Problem Details exception handler
class UnprocessableEntity(APIException):
    """
    HTTP 422 exception for business-rule failures.

    The canonical exception handler serializes this exception using
    the Clinic API Problem Details format.
    """

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The request could not be processed."
    default_code = "unprocessable_entity"


# HTTP 409 exception for state conflicts handled by the canonical Problem Details exception handler
class Conflict(APIException):
    """
    HTTP 409 exception for resource-state conflicts.

    The canonical exception handler serializes this exception using
    the Clinic API Problem Details format.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current resource state."
    default_code = "conflict"


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Shared query-parameter utilities
# ---------------------------------------------------------------------------


def parse_optional_report_date(value, field_name):
    """
    Parse an optional YYYY-MM-DD query parameter.

    Returns None when the parameter is omitted or blank.
    Raises DRF ValidationError for malformed or impossible dates.
    """
    if not value:
        return None

    try:
        parsed = parse_date(value)
    except ValueError:
        parsed = None

    if parsed is None:
        raise ValidationError(
            {
                field_name: (
                    "Date must be a valid calendar date " "using YYYY-MM-DD format."
                )
            }
        )

    return parsed


class ClinicResourceViewSet(viewsets.ViewSet):
    """Shared serialization and elevated clinical-deletion permission."""

    permission_classes = [IsClinicStaff]

    def get_permissions(self):
        return (
            [IsClinicAdmin()] if self.action == "destroy" else super().get_permissions()
        )

    def _serialize(self, instance, many=False):
        return self.serializer_class(instance=instance, many=many)
