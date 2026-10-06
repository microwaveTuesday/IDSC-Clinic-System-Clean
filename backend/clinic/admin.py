"""
Django admin configuration for Clinic-owned domain models.

Student and medicine master data are not registered here because they are
owned by the Registrar and Inventory systems respectively.
"""

from django.contrib import admin

from .models import (
    Consultation,
    HealthRecord,
    HealthStatus,
    MedicineDispensation,
)


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = (
        "health_record_id",
        "student_id",
        "blood_type",
        "height_cm",
        "weight_kg",
        "created_at",
        "updated_at",
    )
    list_filter = ("blood_type",)
    search_fields = (
        "student_id",
        "allergies",
        "medical_history",
        "current_medications",
    )
    ordering = ("-created_at", "-health_record_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        "consultation_id",
        "student_id",
        "chief_complaint",
        "consulted_at",
    )
    search_fields = (
        "student_id",
        "chief_complaint",
        "assessment",
        "treatment",
        "notes",
    )
    ordering = ("-consulted_at", "-consultation_id")
    readonly_fields = (
        "consulted_at",
        "created_at",
        "updated_at",
    )


@admin.register(HealthStatus)
class HealthStatusAdmin(admin.ModelAdmin):
    list_display = (
        "status_id",
        "student_id",
        "status",
        "effective_at",
    )
    list_filter = ("status",)
    search_fields = (
        "student_id",
        "remarks",
    )
    ordering = ("-effective_at", "-status_id")
    readonly_fields = (
        "effective_at",
        "created_at",
        "updated_at",
    )


@admin.register(MedicineDispensation)
class MedicineDispensationAdmin(admin.ModelAdmin):
    list_display = (
        "dispensation_id",
        "student_id",
        "medicine_id",
        "quantity",
        "status",
        "inventory_transaction_id",
        "dispensed_at",
    )
    list_filter = ("status",)
    search_fields = (
        "student_id",
        "medicine_id",
        "inventory_transaction_id",
        "rollback_transaction_id",
        "reason",
    )
    ordering = ("-dispensed_at", "-dispensation_id")
    readonly_fields = (
        "inventory_transaction_id",
        "rollback_transaction_id",
        "dispensed_at",
        "rolled_back_at",
        "created_at",
    )