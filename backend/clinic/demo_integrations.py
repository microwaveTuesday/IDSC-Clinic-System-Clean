"""Owner-operated mock external systems. State is process-local, like the existing mocks."""
from copy import deepcopy
from threading import RLock
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.permissions import IsOwner, IsClinicStaff
from .exceptions import ConflictError
from .services.registrar import registrar_service, StudentNotFoundError
from .services.inventory import inventory_service, MedicineNotFoundError

from .mutations import process_lock, guarded
lock = process_lock
restocks = {}
notifications = []
read_notifications = {}


class StudentWrite(serializers.Serializer):
    student_id = serializers.RegexField(r"^[A-Za-z0-9_-]+$", max_length=64)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    course = serializers.CharField(max_length=80)
    section = serializers.CharField(max_length=80)
    status = serializers.ChoiceField(choices=["ACTIVE", "GRADUATED", "DROPPED_OUT", "INACTIVE"])


class MedicineWrite(serializers.Serializer):
    medicine_id = serializers.RegexField(r"^[A-Za-z0-9_-]+$", max_length=64)
    name = serializers.CharField(max_length=150)
    generic_name = serializers.CharField(max_length=150, allow_blank=True)
    unit = serializers.CharField(max_length=40)
    quantity_in_stock = serializers.IntegerField(min_value=0, max_value=1000000)
    reorder_level = serializers.IntegerField(min_value=0, max_value=1000000)
    status = serializers.ChoiceField(choices=["ACTIVE", "INACTIVE"])
    is_low_stock = serializers.BooleanField(read_only=True)


class StudentLookup(serializers.Serializer):
    student_id = serializers.CharField(max_length=64)


class RestockItem(serializers.Serializer):
    medicine_id = serializers.CharField(max_length=64)
    quantity = serializers.IntegerField(min_value=1, max_value=100000)


class RestockWrite(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["ALL", "SELECTED"])
    quantity = serializers.IntegerField(min_value=1, max_value=100000, default=100)
    items = RestockItem(many=True, required=False, max_length=100)

    def validate(self, attrs):
        if attrs["mode"] == "SELECTED":
            items = attrs.get("items", [])
            if not items:
                raise serializers.ValidationError({"items": "Select at least one medicine."})
            ids = [item["medicine_id"] for item in items]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({"items": "Duplicate medicines are not allowed."})
        return attrs


class RestockResponse(serializers.Serializer):
    request_id = serializers.CharField()
    status = serializers.CharField()
    mode = serializers.CharField()
    requested_by = serializers.CharField()
    created_at = serializers.DateTimeField()
    fulfilled_at = serializers.DateTimeField(allow_null=True)
    items = serializers.ListField(child=serializers.DictField())


class NotificationResponse(serializers.Serializer):
    notification_id = serializers.CharField()
    message = serializers.CharField()
    kind = serializers.CharField()
    created_at = serializers.DateTimeField()


class NotificationRead(serializers.Serializer):
    notification_ids = serializers.ListField(child=serializers.CharField(max_length=64), max_length=200)


class DemoBase(APIView):
    permission_classes = [IsClinicStaff]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if settings.CLINIC_DATA_BACKEND != "mock":
            raise NotFound("These demonstration integrations are available in mock mode only.")


class OwnerDemo(DemoBase):
    permission_classes = [IsOwner]


def notify(kind, message):
    notifications.append({"notification_id": uuid4().hex, "kind": kind, "message": message, "created_at": timezone.now().isoformat()})


def student(student_id):
    try:
        return registrar_service.get_student(student_id)
    except StudentNotFoundError as exc:
        raise NotFound(str(exc)) from exc


def medicine(medicine_id):
    try:
        return inventory_service.get_medicine(medicine_id)
    except MedicineNotFoundError as exc:
        raise NotFound(str(exc)) from exc


class ImportStudentView(DemoBase):
    @extend_schema(request=StudentLookup, responses=StudentWrite)
    @guarded
    def post(self, request):
        serializer = StudentLookup(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Return the current Registrar-owned profile; never create a second identity.
        return Response(student(serializer.validated_data["student_id"]))


class RegistrarStudentsView(OwnerDemo):
    @extend_schema(responses=StudentWrite(many=True))
    def get(self, request):
        with lock:
            return Response(registrar_service.list_students())

    @extend_schema(request=StudentWrite, responses={201: StudentWrite})
    @guarded
    def post(self, request):
        serializer = StudentWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lock:
            row = dict(serializer.validated_data)
            if registrar_service.student_exists(row["student_id"]):
                raise ConflictError("Student ID already exists in Registrar.")
            registrar_service._students = [*registrar_service._students, row]
            return Response(deepcopy(row), status=201)


class RegistrarStudentDetailView(OwnerDemo):
    @extend_schema(request=StudentWrite, responses=StudentWrite)
    @guarded
    def patch(self, request, student_id):
        with lock:
            existing = student(student_id)
            if "student_id" in request.data and request.data["student_id"] != student_id:
                raise ValidationError({"student_id": "Student ID cannot be changed."})
            serializer = StudentWrite(data={**existing, **request.data})
            serializer.is_valid(raise_exception=True)
            row = dict(serializer.validated_data)
            registrar_service._students = [row if old["student_id"] == student_id else old for old in registrar_service._students]
            return Response(row)


class InventoryMedicinesView(OwnerDemo):
    @extend_schema(responses=MedicineWrite(many=True))
    def get(self, request):
        with lock:
            return Response(inventory_service.list_medicines())

    @extend_schema(request=MedicineWrite, responses={201: MedicineWrite})
    @guarded
    def post(self, request):
        serializer = MedicineWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lock:
            row = dict(serializer.validated_data)
            if any(m["medicine_id"] == row["medicine_id"] for m in inventory_service._medicines):
                raise ConflictError("Medicine ID already exists in Inventory.")
            inventory_service._medicines.append(row)
            notify("MEDICINE_ADDED", f"Inventory added {row['name']} ({row['medicine_id']}). It is now available in Medicine stock.")
            return Response(medicine(row["medicine_id"]), status=201)


class InventoryMedicineDetailView(OwnerDemo):
    @extend_schema(request=MedicineWrite, responses=MedicineWrite)
    @guarded
    def patch(self, request, medicine_id):
        with lock:
            existing = medicine(medicine_id)
            if "medicine_id" in request.data and request.data["medicine_id"] != medicine_id:
                raise ValidationError({"medicine_id": "Medicine ID cannot be changed."})
            serializer = MedicineWrite(data={**existing, **request.data})
            serializer.is_valid(raise_exception=True)
            row = dict(serializer.validated_data)
            inventory_service._medicines = [row if old["medicine_id"] == medicine_id else old for old in inventory_service._medicines]
            notify("MEDICINE_UPDATED", f"Inventory updated {row['name']} ({medicine_id}).")
            return Response(medicine(medicine_id))

    @extend_schema(request=None, responses={204: None})
    @guarded
    def delete(self, request, medicine_id):
        with lock:
            medicine(medicine_id)
            if any(t["medicine_id"] == medicine_id for t in inventory_service._transactions.values()):
                raise ConflictError("This medicine has stock transactions. Mark it inactive instead to preserve stock history.")
            if any(r["status"] == "PENDING" and any(i["medicine_id"] == medicine_id for i in r["items"]) for r in restocks.values()):
                raise ConflictError("Fulfill the pending restock request before deleting this medicine.")
            inventory_service._medicines = [m for m in inventory_service._medicines if m["medicine_id"] != medicine_id]
            notify("MEDICINE_REMOVED", f"Inventory removed medicine {medicine_id}.")
            return Response(status=204)


class RestocksView(DemoBase):
    @extend_schema(responses=RestockResponse(many=True))
    def get(self, request):
        with lock:
            return Response(deepcopy(list(reversed(list(restocks.values())))))

    @extend_schema(request=RestockWrite, responses={201: RestockResponse})
    @guarded
    def post(self, request):
        serializer = RestockWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with lock:
            items = data.get("items", []) if data["mode"] == "SELECTED" else [{"medicine_id": m["medicine_id"], "quantity": data["quantity"]} for m in inventory_service.list_medicines(status="ACTIVE")]
            if not items:
                raise ValidationError("There are no active medicines to restock.")
            snapshots = []
            for item in items:
                current = medicine(item["medicine_id"])
                if current["status"] != "ACTIVE":
                    raise ConflictError("Only active medicines can be requested.")
                snapshots.append({**item, "name": current["name"], "unit": current["unit"]})
            row = {"request_id": uuid4().hex, "mode": data["mode"], "status": "PENDING", "items": snapshots, "requested_by": request.user.username, "created_at": timezone.now().isoformat(), "fulfilled_at": None}
            restocks[row["request_id"]] = row
            return Response(deepcopy(row), status=201)


class FulfillRestockView(OwnerDemo):
    @extend_schema(request=None, responses=RestockResponse)
    @guarded
    def post(self, request, request_id):
        with lock:
            row = restocks.get(request_id)
            if row is None:
                raise NotFound("Restock request not found.")
            if row["status"] != "PENDING":
                raise ConflictError("This request has already been fulfilled.")
            # Validate the complete delivery before changing any stock.
            for item in row["items"]:
                current = medicine(item["medicine_id"])
                if current["status"] != "ACTIVE" or current["quantity_in_stock"] + item["quantity"] > 1000000:
                    raise ConflictError("A requested medicine is inactive or exceeds the stock limit. No stock was changed.")
            for item in row["items"]:
                current = next(m for m in inventory_service._medicines if m["medicine_id"] == item["medicine_id"])
                current["quantity_in_stock"] += item["quantity"]
                transaction_id = "RESTOCK-" + uuid4().hex
                inventory_service._transactions[transaction_id] = {"transaction_id": transaction_id, "medicine_id": item["medicine_id"], "quantity": item["quantity"], "type": "RESTOCK", "rolled_back": False}
            row["status"] = "FULFILLED"
            row["fulfilled_at"] = timezone.now().isoformat()
            notify("RESTOCK_FULFILLED", f"Inventory fulfilled restock request {request_id[:8]}.")
            return Response(deepcopy(row))


class InventoryNotificationsView(DemoBase):
    @extend_schema(responses=NotificationResponse(many=True))
    def get(self, request):
        with lock:
            seen = read_notifications.get(request.user.pk, set())
            return Response(deepcopy([n for n in reversed(notifications) if n["notification_id"] not in seen]))

    @extend_schema(request=NotificationRead, responses={204: None})
    @guarded
    def post(self, request):
        serializer = NotificationRead(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lock:
            read_notifications.setdefault(request.user.pk, set()).update(serializer.validated_data["notification_ids"])
        return Response(status=204)
