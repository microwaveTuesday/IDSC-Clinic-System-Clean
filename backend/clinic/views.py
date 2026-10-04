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

from django.db import models, transaction

from django.utils import timezone
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

from .models import (
    Consultation,
    HealthRecord,
    HealthStatus,
    MedicineDispensation,
)
from .serializers import (
    ConsultationSerializer,
    DashboardSerializer,
    HealthRecordSerializer,
    HealthStatusProjectionSerializer,
    HealthStatusSerializer,
    MedicineDispensationSerializer,
    MedicineSerializer,
    StudentSerializer,
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
class HealthView(APIView):
    """Basic Clinic API health endpoint."""

    authentication_classes = []
    permission_classes = []

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
    - Health-record totals come from Clinic.
    - Medicine stock totals come from Inventory.
    - Recent activity comes only from Clinic-owned records.
    """

    RECENT_ACTIVITY_LIMIT = 10

    def get(self, request):
        students = registrar_service.list_students()
        medicines = inventory_service.list_medicines()

        total_students = len(students)

        total_health_records = HealthRecord.objects.count()

        total_medicine_stock = sum(
            medicine["quantity_in_stock"]
            for medicine in medicines
        )

        low_stock_medicines = sum(
            1
            for medicine in medicines
            if medicine["is_low_stock"]
        )

        recent_activity = self._get_recent_activity()

        data = {
            "summary": {
                "total_students": total_students,
                "total_health_records": total_health_records,
                "total_medicine_stock": total_medicine_stock,
                "low_stock_medicines": low_stock_medicines,
            },
            "recent_activity": recent_activity,
        }

        serializer = DashboardSerializer(instance=data)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def _get_recent_activity(self):
        activities = []

        health_records = HealthRecord.objects.order_by(
            "-created_at"
        )[: self.RECENT_ACTIVITY_LIMIT]

        for record in health_records:
            activities.append(
                {
                    "activity_type": "HEALTH_RECORD",
                    "reference_id": record.health_record_id,
                    "student_id": record.student_id,
                    "occurred_at": record.created_at,
                }
            )

        consultations = Consultation.objects.order_by(
            "-consulted_at"
        )[: self.RECENT_ACTIVITY_LIMIT]

        for consultation in consultations:
            activities.append(
                {
                    "activity_type": "CONSULTATION",
                    "reference_id": consultation.consultation_id,
                    "student_id": consultation.student_id,
                    "occurred_at": consultation.consulted_at,
                }
            )

        health_statuses = HealthStatus.objects.order_by(
            "-effective_at"
        )[: self.RECENT_ACTIVITY_LIMIT]

        for health_status in health_statuses:
            activities.append(
                {
                    "activity_type": "HEALTH_STATUS",
                    "reference_id": health_status.status_id,
                    "student_id": health_status.student_id,
                    "occurred_at": health_status.effective_at,
                }
            )

        dispensations = MedicineDispensation.objects.order_by(
            "-dispensed_at"
        )[: self.RECENT_ACTIVITY_LIMIT]

        for dispensation in dispensations:
            activities.append(
                {
                    "activity_type": "MEDICINE_DISPENSATION",
                    "reference_id": dispensation.dispensation_id,
                    "student_id": dispensation.student_id,
                    "occurred_at": dispensation.dispensed_at,
                }
            )

        activities.sort(
            key=lambda activity: activity["occurred_at"],
            reverse=True,
        )

        return activities[: self.RECENT_ACTIVITY_LIMIT]


# ---------------------------------------------------------------------------
# Report utilities
# ---------------------------------------------------------------------------


def parse_optional_report_date(value, field_name):
    """
    Parse an optional YYYY-MM-DD report query parameter.

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


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------
class ClinicVisitsReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Report derived from Clinic-owned consultation records.

    Optional date_from and date_to filters are inclusive and apply
    to the consultation date.
    """

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

        queryset = Consultation.objects.all().order_by(
            "-consulted_at",
            "-consultation_id",
        )

        if date_from:
            queryset = queryset.filter(
                consulted_at__date__gte=date_from
            )

        if date_to:
            queryset = queryset.filter(
                consulted_at__date__lte=date_to
            )

        serializer = ConsultationSerializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "total_visits": queryset.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Health Records
# ---------------------------------------------------------------------------
class HealthRecordsReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Report derived from Clinic-owned health records.

    Optional date_from and date_to filters are inclusive and apply
    to the health record creation date.
    """

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

        queryset = HealthRecord.objects.all().order_by(
            "-created_at",
            "-health_record_id",
        )

        if date_from:
            queryset = queryset.filter(
                created_at__date__gte=date_from
            )

        if date_to:
            queryset = queryset.filter(
                created_at__date__lte=date_to
            )

        serializer = HealthRecordSerializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "total_health_records": queryset.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Medicine Inventory
# ---------------------------------------------------------------------------
class MedicineInventoryReportView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Read-only medicine inventory report obtained through the
    Inventory integration boundary.

    Clinic does not own the medicine catalog or stock represented
    by this report.
    """

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
    Report derived from Clinic-owned medicine dispensation history.

    Supports inclusive dispensation-date filtering together with
    student, medicine, and dispensation-status filters.
    """

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

        queryset = MedicineDispensation.objects.all().order_by(
            "-dispensed_at",
            "-dispensation_id",
        )

        if date_from:
            queryset = queryset.filter(
                dispensed_at__date__gte=date_from
            )

        if date_to:
            queryset = queryset.filter(
                dispensed_at__date__lte=date_to
            )

        if student_id:
            queryset = queryset.filter(
                student_id=student_id
            )

        if medicine_id:
            queryset = queryset.filter(
                medicine_id=medicine_id
            )

        if dispensation_status:
            queryset = queryset.filter(
                status=dispensation_status
            )

        serializer = MedicineDispensationSerializer(
            queryset,
            many=True,
        )

        return Response(
            {
                "total_dispensations": queryset.count(),
                "total_quantity_dispensed": sum(
                    dispensation.quantity
                    for dispensation in queryset
                ),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Registrar projections
# ---------------------------------------------------------------------------
class StudentListView(APIView):
    permission_classes = [IsClinicStaff]
    """
    Read-only student projection backed by Registrar.

    Clinic does not create, update, or delete students.
    """

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

    def get(self, request, student_id):
        try:
            student = registrar_service.get_student(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(StudentSerializer(student).data)


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------
class HealthRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicStaff]
    """CRUD controller for Clinic-owned HealthRecord resources."""

    serializer_class = HealthRecordSerializer
    pagination_class = ClinicPagination
    lookup_field = "health_record_id"

    ORDERING_FIELDS = {
        "health_record_id",
        "student_id",
        "blood_type",
        "created_at",
        "updated_at",
    }

    def get_queryset(self):
        queryset = HealthRecord.objects.all().order_by(
            "-created_at",
            "-health_record_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        blood_type = self.request.query_params.get("blood_type", "").strip()
        search = self.request.query_params.get("search", "").strip()
        ordering = self.request.query_params.get("ordering", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if blood_type:
            queryset = queryset.filter(blood_type__iexact=blood_type)

        if search:
            queryset = queryset.filter(
                models.Q(student_id__icontains=search)
                | models.Q(allergies__icontains=search)
                | models.Q(medical_history__icontains=search)
                | models.Q(current_medications__icontains=search)
            )

        if ordering:
            descending = ordering.startswith("-")
            field = ordering[1:] if descending else ordering

            if field in self.ORDERING_FIELDS:
                queryset = queryset.order_by(ordering)

        return queryset

    def _validate_student(self, student_id):
        try:
            registrar_service.validate_student_for_clinic(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

    def perform_create(self, serializer):
        self._validate_student(serializer.validated_data["student_id"])
        serializer.save()

    def perform_update(self, serializer):
        student_id = serializer.validated_data.get(
            "student_id",
            serializer.instance.student_id,
        )
        self._validate_student(student_id)
        serializer.save()


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------
class ConsultationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicStaff]
    """CRUD controller for Clinic consultation records."""

    serializer_class = ConsultationSerializer
    pagination_class = ClinicPagination
    lookup_field = "consultation_id"

    ORDERING_FIELDS = {
        "consultation_id",
        "student_id",
        "consulted_at",
        "created_at",
        "updated_at",
    }

    def get_queryset(self):
        queryset = Consultation.objects.all().order_by(
            "-consulted_at",
            "-consultation_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        search = self.request.query_params.get("search", "").strip()
        date_from = self.request.query_params.get("date_from", "").strip()
        date_to = self.request.query_params.get("date_to", "").strip()
        ordering = self.request.query_params.get("ordering", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if search:
            queryset = queryset.filter(
                models.Q(chief_complaint__icontains=search)
                | models.Q(assessment__icontains=search)
                | models.Q(treatment__icontains=search)
                | models.Q(notes__icontains=search)
            )

        if date_from:
            queryset = queryset.filter(consulted_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(consulted_at__date__lte=date_to)

        if ordering:
            descending = ordering.startswith("-")
            field = ordering[1:] if descending else ordering

            if field in self.ORDERING_FIELDS:
                queryset = queryset.order_by(ordering)

        return queryset

    def _validate_student(self, student_id):
        try:
            registrar_service.validate_student_for_clinic(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

    def perform_create(self, serializer):
        self._validate_student(serializer.validated_data["student_id"])
        serializer.save()

    def perform_update(self, serializer):
        student_id = serializer.validated_data.get(
            "student_id",
            serializer.instance.student_id,
        )
        self._validate_student(student_id)
        serializer.save()


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------
class HealthStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicStaff]
    """CRUD controller for Clinic-owned HealthStatus resources."""

    serializer_class = HealthStatusSerializer
    pagination_class = ClinicPagination
    lookup_field = "status_id"

    ORDERING_FIELDS = {
        "status_id",
        "student_id",
        "status",
        "effective_at",
        "created_at",
        "updated_at",
    }

    def get_queryset(self):
        queryset = HealthStatus.objects.all().order_by(
            "-effective_at",
            "-status_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        health_status = self.request.query_params.get("status", "").strip()
        date_from = self.request.query_params.get("date_from", "").strip()
        date_to = self.request.query_params.get("date_to", "").strip()
        ordering = self.request.query_params.get("ordering", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if health_status:
            queryset = queryset.filter(status=health_status)

        if date_from:
            queryset = queryset.filter(effective_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(effective_at__date__lte=date_to)

        if ordering:
            descending = ordering.startswith("-")
            field = ordering[1:] if descending else ordering

            if field in self.ORDERING_FIELDS:
                queryset = queryset.order_by(ordering)

        return queryset

    def _validate_student(self, student_id):
        try:
            registrar_service.validate_student_for_clinic(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

    def perform_create(self, serializer):
        self._validate_student(serializer.validated_data["student_id"])
        serializer.save()

    def perform_update(self, serializer):
        student_id = serializer.validated_data.get(
            "student_id",
            serializer.instance.student_id,
        )
        self._validate_student(student_id)
        serializer.save()


# ---------------------------------------------------------------------------
# Inventory projections
# ---------------------------------------------------------------------------
class MedicineListView(APIView):
    permission_classes = [IsClinicStaff]
    """Read-only medicine/stock projection backed by Inventory."""

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

    def get(self, request, medicine_id):
        try:
            medicine = inventory_service.get_medicine(medicine_id)
        except MedicineNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(MedicineSerializer(medicine).data)


# ---------------------------------------------------------------------------
# Medicine dispensing
# ---------------------------------------------------------------------------
class MedicineDispensationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicStaff]
    """
    Clinic-owned medicine dispensation controller.

    Creation validates the student through Registrar, requests Inventory
    stock deduction, and records the returned Inventory transaction ID.

    Update and delete operations are not exposed. Rollback is implemented
    as a dedicated auditable operation.
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

    ORDERING_FIELDS = {
        "dispensation_id",
        "student_id",
        "medicine_id",
        "quantity",
        "status",
        "dispensed_at",
        "created_at",
    }

    def get_queryset(self):
        queryset = MedicineDispensation.objects.all().order_by(
            "-dispensed_at",
            "-dispensation_id",
        )

        student_id = self.request.query_params.get(
            "student_id",
            "",
        ).strip()
        medicine_id = self.request.query_params.get(
            "medicine_id",
            "",
        ).strip()
        dispensation_status = self.request.query_params.get(
            "status",
            "",
        ).strip()
        search = self.request.query_params.get(
            "search",
            "",
        ).strip()
        date_from = self.request.query_params.get(
            "date_from",
            "",
        ).strip()
        date_to = self.request.query_params.get(
            "date_to",
            "",
        ).strip()
        ordering = self.request.query_params.get(
            "ordering",
            "",
        ).strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)

        if dispensation_status:
            queryset = queryset.filter(status=dispensation_status)

        if search:
            queryset = queryset.filter(
                models.Q(student_id__icontains=search)
                | models.Q(medicine_id__icontains=search)
                | models.Q(reason__icontains=search)
                | models.Q(inventory_transaction_id__icontains=search)
                | models.Q(rollback_transaction_id__icontains=search)
            )

        if date_from:
            queryset = queryset.filter(
                dispensed_at__date__gte=date_from
            )

        if date_to:
            queryset = queryset.filter(
                dispensed_at__date__lte=date_to
            )

        if ordering:
            descending = ordering.startswith("-")
            field = ordering[1:] if descending else ordering

            if field in self.ORDERING_FIELDS:
                queryset = queryset.order_by(ordering)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data["student_id"]
        medicine_id = serializer.validated_data["medicine_id"]
        quantity = serializer.validated_data["quantity"]

        try:
            registrar_service.validate_student_for_clinic(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        try:
            inventory_transaction_id = inventory_service.deduct_stock(
                medicine_id,
                quantity,
            )
        except MedicineNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except (MedicineUnavailableError, InsufficientStockError) as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        try:
            with transaction.atomic():
                dispensation = serializer.save(
                    status="COMPLETED",
                    inventory_transaction_id=inventory_transaction_id,
                )
        except Exception:
            try:
                inventory_service.restore_stock(
                    inventory_transaction_id
                )
            except Exception:
                # Preserve the original persistence error as the primary failure
                # if the compensating Inventory operation also fails.
                pass
            raise

        response_serializer = self.get_serializer(dispensation)

        headers = self.get_success_headers(
            response_serializer.data
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="rollback",
    )
    def rollback(self, request, dispensation_id=None):
        """
        Roll back a completed medicine dispensation.

        Inventory restores the stock using the original deduction
        transaction. Clinic then records the rollback transaction and
        preserves the dispensation as an auditable ROLLED_BACK record.
        """

        dispensation = self.get_object()

        if dispensation.status == "ROLLED_BACK":
            raise Conflict(
                detail=(
                    f"Dispensation '{dispensation.dispensation_id}' "
                    "has already been rolled back."
                )
            )

        if not dispensation.inventory_transaction_id:
            raise UnprocessableEntity(
                detail=(
                    f"Dispensation '{dispensation.dispensation_id}' "
                    "does not have an Inventory transaction to roll back."
                )
            )

        try:
            rollback_transaction_id = inventory_service.restore_stock(
                dispensation.inventory_transaction_id
            )
        except InventoryTransactionNotFoundError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc
        except MedicineNotFoundError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc
        except ValueError as exc:
            raise Conflict(detail=str(exc)) from exc

        try:
            with transaction.atomic():
                dispensation.status = "ROLLED_BACK"
                dispensation.rollback_transaction_id = (
                    rollback_transaction_id
                )
                dispensation.rolled_back_at = timezone.now()

                dispensation.save(
                    update_fields=[
                        "status",
                        "rollback_transaction_id",
                        "rolled_back_at",
                    ]
                )
        except Exception:
            # Inventory has already restored stock at this point.
            #
            # A distributed Inventory operation cannot be rolled back by
            # Django's local database transaction. Preserve and surface the
            # resulting failure rather than treating the external operation
            # as though it were reverted.
            raise

        serializer = self.get_serializer(dispensation)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Integration projections
# ---------------------------------------------------------------------------
class HealthStatusIntegrationView(APIView):
    """
    Restricted read-only health-status projection.

    Faculty and Student Portal use separate URLs pointing to this controller.
    Authorization differences are added during the authentication/permission
    phase.
    """

    def get(self, request, student_id):
        try:
            registrar_service.get_student(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        health_status = (
            HealthStatus.objects
            .filter(student_id=student_id)
            .order_by("-effective_at", "-status_id")
            .first()
        )

        if health_status is None:
            return Response(
                {
                    "student_id": student_id,
                    "status": "NOT_AVAILABLE",
                    "remarks": None,
                    "effective_at": None,
                }
            )

        serializer = HealthStatusProjectionSerializer(health_status)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Integration projections
# ---------------------------------------------------------------------------
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


