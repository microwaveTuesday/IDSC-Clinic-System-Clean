"""Focused Clinic HTTP controllers; business rules remain in ClinicService."""

from .view_support import (
    APIView,
    HealthStatusProjectionSerializer,
    IsClinicStaff,
    NotFound,
    Response,
    StudentNotFoundError,
    clinic_service,
    extend_schema,
)


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
            health_status = clinic_service.latest_health_status_for_student(student_id)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

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


class FacultyHealthStatusIntegrationView(HealthStatusIntegrationView):
    """
    Read-only health-status projection for the Faculty module.

    Midterm authorization uses authenticated Clinic sessions.
    A dedicated cross-system trust mechanism can replace this boundary
    when real module-to-module integration is introduced.
    """

    permission_classes = [IsClinicStaff]


class StudentPortalHealthStatusIntegrationView(HealthStatusIntegrationView):
    """
    Read-only health-status projection for the Student Portal module.

    Midterm authorization uses authenticated sessions.
    A dedicated cross-system trust mechanism can replace this boundary
    when real module-to-module integration is introduced.
    """

    permission_classes = [IsClinicStaff]
