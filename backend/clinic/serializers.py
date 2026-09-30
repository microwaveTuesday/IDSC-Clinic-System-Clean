"""
Serializers for the Clinic System API.

Clinic owns:
- HealthRecord
- Consultation
- HealthStatus
- MedicineDispensation

Student identity/profile data is owned by Registrar.
Medicine catalog/stock data is owned by Inventory.

StudentSerializer and MedicineSerializer below are projection serializers for
external service data. They are deliberately not ModelSerializers.
"""

from rest_framework import serializers

from .models import (
    BloodTypeChoices,
    Consultation,
    DispensationStatusChoices,
    HealthRecord,
    HealthStatus,
    HealthStatusChoices,
    MedicineDispensation,
)


# ---------------------------------------------------------------------------
# Clinic-owned resources
# ---------------------------------------------------------------------------


class HealthRecordSerializer(serializers.ModelSerializer):
    """Serializer for Clinic-owned persistent student health information."""

    class Meta:
        model = HealthRecord
        fields = [
            "health_record_id",
            "student_id",
            "blood_type",
            "allergies",
            "medical_history",
            "current_medications",
            "height_cm",
            "weight_kg",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "health_record_id",
            "created_at",
            "updated_at",
        ]

    def validate_student_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("student_id cannot be blank.")
        return value

    def validate_blood_type(self, value):
        if value not in BloodTypeChoices.values:
            valid = ", ".join(BloodTypeChoices.values)
            raise serializers.ValidationError(
                f"Invalid blood type. Valid options are: {valid}"
            )
        return value

    def validate_height_cm(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "height_cm must be greater than 0."
            )
        if value is not None and value > 300:
            raise serializers.ValidationError(
                "height_cm cannot exceed 300 cm."
            )
        return value

    def validate_weight_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "weight_kg must be greater than 0."
            )
        if value is not None and value > 500:
            raise serializers.ValidationError(
                "weight_kg cannot exceed 500 kg."
            )
        return value


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer for Clinic consultation / visit records."""

    class Meta:
        model = Consultation
        fields = [
            "consultation_id",
            "student_id",
            "chief_complaint",
            "assessment",
            "treatment",
            "notes",
            "consulted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "consultation_id",
            "consulted_at",
            "created_at",
            "updated_at",
        ]

    def validate_student_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("student_id cannot be blank.")
        return value

    def validate_chief_complaint(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "chief_complaint cannot be blank."
            )
        return value


class HealthStatusSerializer(serializers.ModelSerializer):
    """Serializer for Clinic-owned student health status."""

    class Meta:
        model = HealthStatus
        fields = [
            "status_id",
            "student_id",
            "status",
            "remarks",
            "effective_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status_id",
            "effective_at",
            "created_at",
            "updated_at",
        ]

    def validate_student_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("student_id cannot be blank.")
        return value

    def validate_status(self, value):
        if value not in HealthStatusChoices.values:
            valid = ", ".join(HealthStatusChoices.values)
            raise serializers.ValidationError(
                f"Invalid health status. Valid options are: {valid}"
            )
        return value


class MedicineDispensationSerializer(serializers.ModelSerializer):
    """
    Serializer for Clinic-owned medicine dispensation records.

    Inventory owns medicine stock. inventory_transaction_id is populated by
    the dispensing orchestration/service after Inventory accepts the stock
    deduction.
    """

    class Meta:
        model = MedicineDispensation
        fields = [
            "dispensation_id",
            "student_id",
            "medicine_id",
            "quantity",
            "reason",
            "status",
            "inventory_transaction_id",
            "rollback_transaction_id",
            "dispensed_at",
            "rolled_back_at",
            "created_at",
        ]
        read_only_fields = [
            "dispensation_id",
            "status",
            "inventory_transaction_id",
            "rollback_transaction_id",
            "dispensed_at",
            "rolled_back_at",
            "created_at",
        ]

    def validate_student_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("student_id cannot be blank.")
        return value

    def validate_medicine_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("medicine_id cannot be blank.")
        return value

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "quantity must be greater than or equal to 1."
            )
        return value


# ---------------------------------------------------------------------------
# External service projections
# ---------------------------------------------------------------------------


class StudentSerializer(serializers.Serializer):
    """
    Read-only projection of student data owned by Registrar.

    This serializer has no Clinic ORM model and must never create, update,
    or delete students.
    """

    student_id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    course = serializers.CharField(read_only=True)
    section = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)


class MedicineSerializer(serializers.Serializer):
    """
    Read-only projection of medicine/stock data owned by Inventory.

    This serializer has no Clinic ORM model and must never mutate Inventory
    master data.
    """

    medicine_id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    generic_name = serializers.CharField(read_only=True)
    unit = serializers.CharField(read_only=True)
    quantity_in_stock = serializers.IntegerField(read_only=True)
    reorder_level = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)


# ---------------------------------------------------------------------------
# Integration / aggregate response schemas
# ---------------------------------------------------------------------------


class HealthStatusProjectionSerializer(serializers.Serializer):
    """Restricted health-status response for Faculty and Student Portal."""

    student_id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    remarks = serializers.CharField(read_only=True)
    effective_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
    )


class DashboardSummarySerializer(serializers.Serializer):
    total_students = serializers.IntegerField(read_only=True)
    total_health_records = serializers.IntegerField(read_only=True)
    total_medicine_stock = serializers.IntegerField(read_only=True)
    low_stock_medicines = serializers.IntegerField(read_only=True)


class RecentActivitySerializer(serializers.Serializer):
    activity_type = serializers.CharField(read_only=True)
    reference_id = serializers.IntegerField(read_only=True)
    student_id = serializers.CharField(read_only=True)
    occurred_at = serializers.DateTimeField(read_only=True)


class DashboardSerializer(serializers.Serializer):
    summary = DashboardSummarySerializer(read_only=True)
    recent_activity = RecentActivitySerializer(
        many=True,
        read_only=True,
    )