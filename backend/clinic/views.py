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

from django.db import models
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Consultation,
    HealthRecord,
    HealthStatus,
    MedicineDispensation,
)
from .serializers import (
    ConsultationSerializer,
    HealthRecordSerializer,
    HealthStatusProjectionSerializer,
    HealthStatusSerializer,
    MedicineDispensationSerializer,
    MedicineSerializer,
    StudentSerializer,
)
from .services.inventory import (
    MedicineNotFoundError,
    inventory_service,
)
from .services.registrar import (
    StudentNotFoundError,
    registrar_service,
)


# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------


class HealthView(APIView):
    """Basic Clinic API health endpoint."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "status": "healthy",
                "service": "clinic",
                "version": "1.0.0",
            }
        )


# ---------------------------------------------------------------------------
# Registrar projections
# ---------------------------------------------------------------------------


class StudentListView(APIView):
    """
    Read-only student projection backed by Registrar.

    Clinic does not create, update, or delete students.
    """

    def get(self, request):
        search = request.query_params.get("search")
        students = registrar_service.list_students(search=search)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)


class StudentDetailView(APIView):
    """Retrieve one student from the Registrar boundary."""

    def get(self, request, student_id):
        try:
            student = registrar_service.get_student(student_id)
        except StudentNotFoundError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(StudentSerializer(student).data)


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------


class HealthRecordViewSet(viewsets.ModelViewSet):
    """CRUD controller for Clinic-owned HealthRecord resources."""

    serializer_class = HealthRecordSerializer
    lookup_field = "health_record_id"

    def get_queryset(self):
        queryset = HealthRecord.objects.all().order_by(
            "-created_at",
            "-health_record_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        blood_type = self.request.query_params.get("blood_type", "").strip()
        search = self.request.query_params.get("search", "").strip()

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

        return queryset


class ConsultationViewSet(viewsets.ModelViewSet):
    """CRUD controller for Clinic consultation records."""

    serializer_class = ConsultationSerializer
    lookup_field = "consultation_id"

    def get_queryset(self):
        queryset = Consultation.objects.all().order_by(
            "-consulted_at",
            "-consultation_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        return queryset


class HealthStatusViewSet(viewsets.ModelViewSet):
    """CRUD controller for Clinic-owned HealthStatus resources."""

    serializer_class = HealthStatusSerializer
    lookup_field = "status_id"

    def get_queryset(self):
        queryset = HealthStatus.objects.all().order_by(
            "-effective_at",
            "-status_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        health_status = self.request.query_params.get("status", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if health_status:
            queryset = queryset.filter(status=health_status)

        return queryset


# ---------------------------------------------------------------------------
# Inventory projections
# ---------------------------------------------------------------------------


class MedicineListView(APIView):
    """Read-only medicine/stock projection backed by Inventory."""

    def get(self, request):
        search = request.query_params.get("search")
        medicines = inventory_service.list_medicines(search=search)
        serializer = MedicineSerializer(medicines, many=True)
        return Response(serializer.data)


class MedicineDetailView(APIView):
    """Retrieve one medicine from the Inventory boundary."""

    def get(self, request, medicine_id):
        try:
            medicine = inventory_service.get_medicine(medicine_id)
        except MedicineNotFoundError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(MedicineSerializer(medicine).data)


# ---------------------------------------------------------------------------
# Medicine dispensing
# ---------------------------------------------------------------------------


class MedicineDispensationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Structural controller for medicine dispensation records.

    Creation and rollback require Registrar + Inventory orchestration and are
    completed in Phase 5 rather than embedding external ownership logic here.
    """

    serializer_class = MedicineDispensationSerializer
    lookup_field = "dispensation_id"

    def get_queryset(self):
        queryset = MedicineDispensation.objects.all().order_by(
            "-dispensed_at",
            "-dispensation_id",
        )

        student_id = self.request.query_params.get("student_id", "").strip()
        medicine_id = self.request.query_params.get("medicine_id", "").strip()

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)

        return queryset


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
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

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
                    "remarks": "",
                    "effective_at": None,
                }
            )

        serializer = HealthStatusProjectionSerializer(health_status)
        return Response(serializer.data)