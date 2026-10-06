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

from authentication.permissions import IsClinicStaff

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
                    "Date must be a valid calendar date "
                    "using YYYY-MM-DD format."
                )
            }
        )

    return parsed


class HealthView(APIView):
    """Basic Clinic API health endpoint."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        operation_id="clinic_health_check",
        responses=HealthCheckSerializer,
    )
    def get(self, request):
        return Response({"status": "ok"})


# ---------------------------------------------------------------------------
# Clinic dashboard
# ---------------------------------------------------------------------------
class DashboardView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Aggregated Clinic dashboard.

    Data ownership:
    - Student totals come from Registrar.
    - Health-record totals come through ClinicService.
    - Medicine stock totals come from Inventory.
    - Recent activity comes through ClinicService.
    """

    RECENT_ACTIVITY_LIMIT = 10

    @extend_schema(
        responses=DashboardSerializer,
    )
    def get(self, request):
        students = registrar_service.list_students()
        medicines = inventory_service.list_medicines()

        total_students = len(students)

        total_health_records = (
            clinic_service.total_health_records()
        )

        total_medicine_stock = sum(
            medicine["quantity_in_stock"]
            for medicine in medicines
        )

        low_stock_medicines = sum(
            1
            for medicine in medicines
            if medicine["is_low_stock"]
        )

        recent_activity = clinic_service.recent_activity(
            self.RECENT_ACTIVITY_LIMIT
        )

        data = {
            "summary": {
                "total_students": total_students,
                "total_health_records": total_health_records,
                "total_medicine_stock": total_medicine_stock,
                "low_stock_medicines": low_stock_medicines,
            },
            "recent_activity": recent_activity,
        }

        serializer = DashboardSerializer(
            instance=data
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class ClinicVisitsReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Report derived from Clinic-owned consultation mock data.

    Optional date_from and date_to filters are inclusive.
    """

    @extend_schema(
        responses=ClinicVisitsReportSerializer,
    )
    def get(self, request):
        date_from_raw = request.query_params.get(
            "date_from",
            "",
        ).strip()

        date_to_raw = request.query_params.get(
            "date_to",
            "",
        ).strip()

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                {
                    "date_range": (
                        "date_from must be earlier than or equal "
                        "to date_to."
                    )
                }
            )

        records = clinic_service.report_consultations(
            date_from=date_from,
            date_to=date_to,
        )

        serializer = ConsultationSerializer(
            records,
            many=True,
        )

        return Response(
            {
                "total_visits": len(records),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class HealthRecordsReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Report derived from Clinic-owned health-record mock data.

    Optional date_from and date_to filters are inclusive.
    """

    @extend_schema(
        responses=HealthRecordsReportSerializer,
    )
    def get(self, request):
        date_from_raw = request.query_params.get(
            "date_from",
            "",
        ).strip()

        date_to_raw = request.query_params.get(
            "date_to",
            "",
        ).strip()

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                {
                    "date_range": (
                        "date_from must be earlier than or equal "
                        "to date_to."
                    )
                }
            )

        records = clinic_service.report_health_records(
            date_from=date_from,
            date_to=date_to,
        )

        serializer = HealthRecordSerializer(
            records,
            many=True,
        )

        return Response(
            {
                "total_health_records": len(records),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class MedicineInventoryReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Read-only medicine inventory report obtained through the
    Inventory integration boundary.

    Clinic does not own the medicine catalog or stock represented
    by this report.
    """

    @extend_schema(
        responses=MedicineInventoryReportSerializer,
    )
    def get(self, request):
        low_stock_raw = request.query_params.get("low_stock")
        status_filter = request.query_params.get("status")

        low_stock = self._parse_optional_boolean(
            low_stock_raw,
            "low_stock",
        )

        medicines = inventory_service.list_medicines(
            low_stock=low_stock,
            status=status_filter,
        )

        serializer = MedicineSerializer(
            medicines,
            many=True,
        )

        return Response(
            {
                "total_medicines": len(medicines),
                "total_stock": sum(
                    medicine["quantity_in_stock"]
                    for medicine in medicines
                ),
                "low_stock_medicines": sum(
                    1
                    for medicine in medicines
                    if medicine["is_low_stock"]
                ),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _parse_optional_boolean(value, field_name):
        if value is None or value == "":
            return None

        normalized = str(value).strip().lower()

        if normalized == "true":
            return True

        if normalized == "false":
            return False

        raise ValidationError(
            {
                field_name: (
                    "Value must be either true or false."
                )
            }
        )


# ---------------------------------------------------------------------------
# Medicine Dispensation
# ---------------------------------------------------------------------------
class MedicineDispensationReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Report derived from Clinic-owned medicine-dispensation mock data.
    """

    @extend_schema(
        responses=MedicineDispensationReportSerializer,
    )
    def get(self, request):
        date_from_raw = request.query_params.get(
            "date_from",
            "",
        ).strip()

        date_to_raw = request.query_params.get(
            "date_to",
            "",
        ).strip()

        student_id = request.query_params.get(
            "student_id",
            "",
        ).strip()

        medicine_id = request.query_params.get(
            "medicine_id",
            "",
        ).strip()

        dispensation_status = request.query_params.get(
            "status",
            "",
        ).strip()

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                {
                    "date_range": (
                        "date_from must be earlier than or equal "
                        "to date_to."
                    )
                }
            )

        records = clinic_service.report_dispensations(
            date_from=date_from,
            date_to=date_to,
            student_id=student_id,
            medicine_id=medicine_id,
            status=dispensation_status,
        )

        serializer = MedicineDispensationSerializer(
            records,
            many=True,
        )

        return Response(
            {
                "total_dispensations": len(records),
                "total_quantity_dispensed": sum(
                    row["quantity"]
                    for row in records
                ),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class StudentListView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Read-only student projection backed by Registrar.

    Clinic does not create, update, or delete students.
    """

    @extend_schema(
        operation_id="clinic_student_list",
        responses=PaginatedStudentSerializer,
    )
    def get(self, request):
        search = request.query_params.get("search")
        student_status = request.query_params.get("status")
        course = request.query_params.get("course")
        section = request.query_params.get("section")

        students = registrar_service.list_students(
            search=search,
            status=student_status,
            course=course,
            section=section,
        )

        paginator = ClinicPagination()
        page = paginator.paginate_queryset(students, request, view=self)

        serializer = StudentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StudentDetailView(APIView):
    permission_classes = [IsClinicStaff]
    """Retrieve one student from the Registrar boundary."""

    @extend_schema(
        operation_id="clinic_student_retrieve",
        responses=StudentSerializer,
    )
    def get(self, request, student_id):
        try:
            student = registrar_service.get_student(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(StudentSerializer(student).data)


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------
@extend_schema_view(
    retrieve=_int64_path_schema(
        "health_record_id",
        "Clinic-owned health record identifier.",
    ),
    update=_int64_path_schema(
        "health_record_id",
        "Clinic-owned health record identifier.",
    ),
    partial_update=_int64_path_schema(
        "health_record_id",
        "Clinic-owned health record identifier.",
    ),
    destroy=_int64_path_schema(
        "health_record_id",
        "Clinic-owned health record identifier.",
    ),
)
class HealthRecordViewSet(viewsets.ViewSet):
    permission_classes = [IsClinicStaff]
    """
    CRUD controller for Clinic-owned HealthRecord mock resources.

    Route/controller responsibilities:
    - parse request/query parameters
    - validate payloads with the canonical serializer
    - delegate domain operations to ClinicService

    Persistence/data access belongs to ClinicService -> data layer.
    """

    serializer_class = HealthRecordSerializer
    pagination_class = ClinicPagination
    lookup_field = "health_record_id"

    def _serialize(self, instance, many=False):
        return self.serializer_class(
            instance=instance,
            many=many,
        )

    def _get_record(self, health_record_id):
        try:
            return clinic_service.get_health_record(
                health_record_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

    def list(self, request):
        records = clinic_service.list_health_records(
            student_id=request.query_params.get(
                "student_id",
                "",
            ).strip(),
            blood_type=request.query_params.get(
                "blood_type",
                "",
            ).strip(),
            search=request.query_params.get(
                "search",
                "",
            ).strip(),
            ordering=request.query_params.get(
                "ordering",
                "",
            ).strip(),
        )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            records,
            request,
            view=self,
        )

        serializer = self._serialize(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def retrieve(
        self,
        request,
        health_record_id=None,
    ):
        record = self._get_record(
            health_record_id
        )

        return Response(
            self._serialize(record).data
        )

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .create_health_record(
                    serializer.validated_data
                )
            )
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        output = self._serialize(record)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request,
        health_record_id=None,
    ):
        return self._update(
            request,
            health_record_id,
            partial=False,
        )

    def partial_update(
        self,
        request,
        health_record_id=None,
    ):
        return self._update(
            request,
            health_record_id,
            partial=True,
        )

    def _update(
        self,
        request,
        health_record_id,
        partial,
    ):
        current = self._get_record(
            health_record_id
        )

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .update_health_record(
                    health_record_id,
                    serializer.validated_data,
                )
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data
        )

    def destroy(
        self,
        request,
        health_record_id=None,
    ):
        try:
            clinic_service.delete_health_record(
                health_record_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    retrieve=_int64_path_schema(
        "consultation_id",
        "Clinic-owned consultation identifier.",
    ),
    update=_int64_path_schema(
        "consultation_id",
        "Clinic-owned consultation identifier.",
    ),
    partial_update=_int64_path_schema(
        "consultation_id",
        "Clinic-owned consultation identifier.",
    ),
    destroy=_int64_path_schema(
        "consultation_id",
        "Clinic-owned consultation identifier.",
    ),
)
class ConsultationViewSet(viewsets.ViewSet):
    permission_classes = [IsClinicStaff]
    """CRUD controller for Clinic consultation mock resources."""

    serializer_class = ConsultationSerializer
    pagination_class = ClinicPagination
    lookup_field = "consultation_id"

    def _serialize(self, instance, many=False):
        return self.serializer_class(
            instance=instance,
            many=many,
        )

    def _get_record(self, consultation_id):
        try:
            return clinic_service.get_consultation(
                consultation_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

    def list(self, request):
        date_from_raw = (
            request.query_params.get(
                "date_from",
                "",
            ).strip()
        )

        date_to_raw = (
            request.query_params.get(
                "date_to",
                "",
            ).strip()
        )

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        records = clinic_service.list_consultations(
            student_id=request.query_params.get(
                "student_id",
                "",
            ).strip(),
            search=request.query_params.get(
                "search",
                "",
            ).strip(),
            date_from=date_from,
            date_to=date_to,
            ordering=request.query_params.get(
                "ordering",
                "",
            ).strip(),
        )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            records,
            request,
            view=self,
        )

        serializer = self._serialize(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def retrieve(
        self,
        request,
        consultation_id=None,
    ):
        record = self._get_record(
            consultation_id
        )

        return Response(
            self._serialize(record).data
        )

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .create_consultation(
                    serializer.validated_data
                )
            )
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request,
        consultation_id=None,
    ):
        return self._update(
            request,
            consultation_id,
            partial=False,
        )

    def partial_update(
        self,
        request,
        consultation_id=None,
    ):
        return self._update(
            request,
            consultation_id,
            partial=True,
        )

    def _update(
        self,
        request,
        consultation_id,
        partial,
    ):
        current = self._get_record(
            consultation_id
        )

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .update_consultation(
                    consultation_id,
                    serializer.validated_data,
                )
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data
        )

    def destroy(
        self,
        request,
        consultation_id=None,
    ):
        try:
            clinic_service.delete_consultation(
                consultation_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema_view(
    retrieve=_int64_path_schema(
        "status_id",
        "Clinic-owned health status identifier.",
    ),
    update=_int64_path_schema(
        "status_id",
        "Clinic-owned health status identifier.",
    ),
    partial_update=_int64_path_schema(
        "status_id",
        "Clinic-owned health status identifier.",
    ),
    destroy=_int64_path_schema(
        "status_id",
        "Clinic-owned health status identifier.",
    ),
)
class HealthStatusViewSet(viewsets.ViewSet):
    permission_classes = [IsClinicStaff]
    """CRUD controller for Clinic-owned HealthStatus mock resources."""

    serializer_class = HealthStatusSerializer
    pagination_class = ClinicPagination
    lookup_field = "status_id"

    def _serialize(self, instance, many=False):
        return self.serializer_class(
            instance=instance,
            many=many,
        )

    def _get_record(self, status_id):
        try:
            return clinic_service.get_health_status(
                status_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

    def list(self, request):
        date_from_raw = (
            request.query_params.get(
                "date_from",
                "",
            ).strip()
        )

        date_to_raw = (
            request.query_params.get(
                "date_to",
                "",
            ).strip()
        )

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        records = clinic_service.list_health_statuses(
            student_id=request.query_params.get(
                "student_id",
                "",
            ).strip(),
            status=request.query_params.get(
                "status",
                "",
            ).strip(),
            date_from=date_from,
            date_to=date_to,
            ordering=request.query_params.get(
                "ordering",
                "",
            ).strip(),
        )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            records,
            request,
            view=self,
        )

        serializer = self._serialize(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def retrieve(
        self,
        request,
        status_id=None,
    ):
        record = self._get_record(
            status_id
        )

        return Response(
            self._serialize(record).data
        )

    def create(self, request):
        serializer = self.serializer_class(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .create_health_status(
                    serializer.validated_data
                )
            )
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request,
        status_id=None,
    ):
        return self._update(
            request,
            status_id,
            partial=False,
        )

    def partial_update(
        self,
        request,
        status_id=None,
    ):
        return self._update(
            request,
            status_id,
            partial=True,
        )

    def _update(
        self,
        request,
        status_id,
        partial,
    ):
        current = self._get_record(
            status_id
        )

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = (
                clinic_service
                .update_health_status(
                    status_id,
                    serializer.validated_data,
                )
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data
        )

    def destroy(
        self,
        request,
        status_id=None,
    ):
        try:
            clinic_service.delete_health_status(
                status_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class MedicineListView(APIView):
    permission_classes = [IsClinicStaff]
    """Read-only medicine/stock projection backed by Inventory."""

    @extend_schema(
        operation_id="clinic_medicine_list",
        responses=PaginatedMedicineSerializer,
    )
    def get(self, request):
        search = request.query_params.get("search")
        low_stock = request.query_params.get("low_stock")
        medicine_status = request.query_params.get("status")
        ordering = request.query_params.get("ordering")

        parsed_low_stock = None

        if low_stock is not None:
            normalized = low_stock.strip().lower()

            if normalized == "true":
                parsed_low_stock = True
            elif normalized == "false":
                parsed_low_stock = False
            else:
                raise ValidationError(
                    {
                        "low_stock": [
                            "low_stock must be either true or false."
                        ]
                    }
                )

        medicines = inventory_service.list_medicines(
            search=search,
            low_stock=parsed_low_stock,
            status=medicine_status,
            ordering=ordering,
        )

        paginator = ClinicPagination()
        page = paginator.paginate_queryset(
            medicines,
            request,
            view=self,
        )

        serializer = MedicineSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ---------------------------------------------------------------------------
# Inventory projections
# ---------------------------------------------------------------------------
class MedicineDetailView(APIView):
    permission_classes = [IsClinicStaff]
    """Retrieve one medicine from the Inventory boundary."""

    @extend_schema(
        operation_id="clinic_medicine_retrieve",
        responses=MedicineSerializer,
    )
    def get(self, request, medicine_id):
        try:
            medicine = inventory_service.get_medicine(medicine_id)
        except MedicineNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(MedicineSerializer(medicine).data)


# ---------------------------------------------------------------------------
# Medicine dispensing
# ---------------------------------------------------------------------------
@extend_schema_view(
    retrieve=_int64_path_schema(
        "dispensation_id",
        "Clinic-owned medicine dispensation identifier.",
    ),
    rollback=_int64_path_schema(
        "dispensation_id",
        "Clinic-owned medicine dispensation identifier.",
    ),
)
class MedicineDispensationViewSet(viewsets.ViewSet):
    permission_classes = [IsClinicStaff]
    """
    Clinic-owned medicine-dispensation controller.

    The controller validates HTTP input and delegates business
    orchestration to ClinicService.

    ClinicService coordinates:
    Registrar -> Inventory -> Clinic data layer.
    """

    serializer_class = MedicineDispensationSerializer
    pagination_class = ClinicPagination
    lookup_field = "dispensation_id"

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    def _serialize(
        self,
        instance,
        many=False,
    ):
        return self.serializer_class(
            instance=instance,
            many=many,
        )

    def _get_record(
        self,
        dispensation_id,
    ):
        try:
            return clinic_service.get_dispensation(
                dispensation_id
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

    def list(self, request):
        date_from_raw = (
            request.query_params.get(
                "date_from",
                "",
            ).strip()
        )

        date_to_raw = (
            request.query_params.get(
                "date_to",
                "",
            ).strip()
        )

        date_from = parse_optional_report_date(
            date_from_raw,
            "date_from",
        )

        date_to = parse_optional_report_date(
            date_to_raw,
            "date_to",
        )

        records = clinic_service.list_dispensations(
            student_id=request.query_params.get(
                "student_id",
                "",
            ).strip(),
            medicine_id=request.query_params.get(
                "medicine_id",
                "",
            ).strip(),
            status=request.query_params.get(
                "status",
                "",
            ).strip(),
            search=request.query_params.get(
                "search",
                "",
            ).strip(),
            date_from=date_from,
            date_to=date_to,
            ordering=request.query_params.get(
                "ordering",
                "",
            ).strip(),
        )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            records,
            request,
            view=self,
        )

        serializer = self._serialize(
            page,
            many=True,
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def retrieve(
        self,
        request,
        dispensation_id=None,
    ):
        record = self._get_record(
            dispensation_id
        )

        return Response(
            self._serialize(record).data
        )

    def create(
        self,
        request,
    ):
        serializer = self.serializer_class(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            record = clinic_service.create_dispensation(
                serializer.validated_data
            )
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc
        except MedicineNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except (
            MedicineUnavailableError,
            InsufficientStockError,
        ) as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="rollback",
    )
    def rollback(
        self,
        request,
        dispensation_id=None,
    ):
        try:
            record = (
                clinic_service
                .rollback_dispensation(
                    dispensation_id
                )
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc
        except (
            ClinicDispensationAlreadyRolledBackError
        ) as exc:
            raise Conflict(
                detail=str(exc)
            ) from exc
        except (
            ClinicDispensationRollbackUnavailableError
        ) as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc
        except (
            InventoryTransactionNotFoundError,
            MedicineNotFoundError,
        ) as exc:
            raise UnprocessableEntity(
                detail=str(exc)
            ) from exc
        except ValueError as exc:
            raise Conflict(
                detail=str(exc)
            ) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Integration projections
# ---------------------------------------------------------------------------
class HealthStatusIntegrationView(APIView):
    """
    Restricted read-only health-status projection.

    Faculty and Student Portal use separate URLs pointing to this
    controller. Clinic-owned status data is read through ClinicService.
    """

    @extend_schema(
        responses=HealthStatusProjectionSerializer,
    )
    def get(self, request, student_id):
        try:
            health_status = (
                clinic_service.latest_health_status_for_student(
                    student_id
                )
            )
        except StudentNotFoundError as exc:
            raise NotFound(
                detail=str(exc)
            ) from exc

        if health_status is None:
            return Response(
                {
                    "student_id": student_id,
                    "status": "NOT_AVAILABLE",
                    "remarks": None,
                    "effective_at": None,
                }
            )

        serializer = HealthStatusProjectionSerializer(
            health_status
        )

        return Response(serializer.data)


class FacultyHealthStatusIntegrationView(HealthStatusIntegrationView):
    """
    Read-only health-status projection for the Faculty module.

    Midterm authorization uses authenticated Clinic sessions.
    A dedicated cross-system trust mechanism can replace this boundary
    when real module-to-module integration is introduced.
    """

    permission_classes = [IsAuthenticated]

class StudentPortalHealthStatusIntegrationView(HealthStatusIntegrationView):
    """
    Read-only health-status projection for the Student Portal module.

    Midterm authorization uses authenticated sessions.
    A dedicated cross-system trust mechanism can replace this boundary
    when real module-to-module integration is introduced.
    """

    permission_classes = [IsAuthenticated]


