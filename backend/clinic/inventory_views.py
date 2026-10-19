"""Focused Clinic HTTP controllers; business rules remain in ClinicService."""
from .view_support import (
    APIView,
    ClinicDispensationAlreadyRolledBackError,
    ClinicDispensationRollbackUnavailableError,
    ClinicPagination,
    ClinicResourceNotFoundError,
    ClinicResourceViewSet,
    Conflict,
    InsufficientStockError,
    InventoryTransactionNotFoundError,
    IsClinicStaff,
    MedicineDispensationSerializer,
    MedicineNotFoundError,
    MedicineSerializer,
    MedicineUnavailableError,
    NotFound,
    OpenApiParameter,
    OpenApiTypes,
    PaginatedMedicineSerializer,
    Response,
    StudentNotFoundError,
    StudentUnavailableError,
    UnprocessableEntity,
    ValidationError,
    _int64_path_schema,
    action,
    clinic_service,
    extend_schema,
    extend_schema_view,
    guarded,
    inventory_service,
    parse_optional_report_date,
    status,
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
class MedicineDispensationViewSet(ClinicResourceViewSet):
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
        "delete",
    ]

    @extend_schema(request=None, responses={204: None}, parameters=[OpenApiParameter(name="dispensation_id", type=OpenApiTypes.INT64, location=OpenApiParameter.PATH)])
    @guarded
    def destroy(self, request, dispensation_id=None):
        record = clinic_service.repository.get_dispensation(dispensation_id)
        if record is None:
            raise NotFound("Dispensing history not found.")
        # History removal never changes the already completed Inventory transaction.
        clinic_service.repository.delete_dispensation(dispensation_id)
        return Response(status=204)


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

    @guarded
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
    @guarded
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
