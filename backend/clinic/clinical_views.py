"""Focused Clinic HTTP controllers; business rules remain in ClinicService."""

from .view_support import (
    ClinicPagination,
    ClinicResourceNotFoundError,
    ClinicResourceViewSet,
    ConsultationSerializer,
    HealthRecordSerializer,
    HealthStatusSerializer,
    IsClinicStaff,
    NotFound,
    Response,
    StudentNotFoundError,
    StudentUnavailableError,
    UnprocessableEntity,
    _int64_path_schema,
    clinic_service,
    extend_schema_view,
    guarded,
    parse_optional_report_date,
    status,
)


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
class HealthRecordViewSet(ClinicResourceViewSet):
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

    def _get_record(self, health_record_id):
        try:
            return clinic_service.get_health_record(health_record_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

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

        return paginator.get_paginated_response(serializer.data)

    def retrieve(
        self,
        request,
        health_record_id=None,
    ):
        record = self._get_record(health_record_id)

        return Response(self._serialize(record).data)

    @guarded
    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.create_health_record(serializer.validated_data)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        output = self._serialize(record)

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    @guarded
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

    @guarded
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
        current = self._get_record(health_record_id)

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.update_health_record(
                health_record_id,
                serializer.validated_data,
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        return Response(self._serialize(record).data)

    @guarded
    def destroy(
        self,
        request,
        health_record_id=None,
    ):
        try:
            clinic_service.delete_health_record(health_record_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)


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
class ConsultationViewSet(ClinicResourceViewSet):
    permission_classes = [IsClinicStaff]

    """CRUD controller for Clinic consultation mock resources."""

    serializer_class = ConsultationSerializer
    pagination_class = ClinicPagination
    lookup_field = "consultation_id"

    def _get_record(self, consultation_id):
        try:
            return clinic_service.get_consultation(consultation_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

    def list(self, request):
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

        return paginator.get_paginated_response(serializer.data)

    def retrieve(
        self,
        request,
        consultation_id=None,
    ):
        record = self._get_record(consultation_id)

        return Response(self._serialize(record).data)

    @guarded
    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.create_consultation(serializer.validated_data)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_201_CREATED,
        )

    @guarded
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

    @guarded
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
        current = self._get_record(consultation_id)

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.update_consultation(
                consultation_id,
                serializer.validated_data,
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        return Response(self._serialize(record).data)

    @guarded
    def destroy(
        self,
        request,
        consultation_id=None,
    ):
        try:
            clinic_service.delete_consultation(consultation_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)


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
class HealthStatusViewSet(ClinicResourceViewSet):
    permission_classes = [IsClinicStaff]

    """CRUD controller for Clinic-owned HealthStatus mock resources."""

    serializer_class = HealthStatusSerializer
    pagination_class = ClinicPagination
    lookup_field = "status_id"

    def _get_record(self, status_id):
        try:
            return clinic_service.get_health_status(status_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

    def list(self, request):
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

        return paginator.get_paginated_response(serializer.data)

    def retrieve(
        self,
        request,
        status_id=None,
    ):
        record = self._get_record(status_id)

        return Response(self._serialize(record).data)

    @guarded
    def create(self, request):
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.create_health_status(serializer.validated_data)
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        return Response(
            self._serialize(record).data,
            status=status.HTTP_201_CREATED,
        )

    @guarded
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

    @guarded
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
        current = self._get_record(status_id)

        serializer = self.serializer_class(
            instance=current,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        try:
            record = clinic_service.update_health_status(
                status_id,
                serializer.validated_data,
            )
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc
        except StudentUnavailableError as exc:
            raise UnprocessableEntity(detail=str(exc)) from exc

        return Response(self._serialize(record).data)

    @guarded
    def destroy(
        self,
        request,
        status_id=None,
    ):
        try:
            clinic_service.delete_health_status(status_id)
        except ClinicResourceNotFoundError as exc:
            raise NotFound(detail=str(exc)) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)
