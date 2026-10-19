"""Focused Clinic HTTP controllers; business rules remain in ClinicService."""
from .view_support import (
    APIView,
    ClinicPagination,
    ClinicVisitsReportSerializer,
    ConsultationSerializer,
    DashboardSerializer,
    HealthCheckSerializer,
    HealthRecordSerializer,
    HealthRecordsReportSerializer,
    IsClinicStaff,
    MedicineDispensationReportSerializer,
    MedicineDispensationSerializer,
    MedicineInventoryReportSerializer,
    MedicineSerializer,
    NotFound,
    PaginatedStudentSerializer,
    Response,
    StudentNotFoundError,
    StudentSerializer,
    ValidationError,
    clinic_service,
    extend_schema,
    inventory_service,
    parse_optional_report_date,
    registrar_service,
    status,
)

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
