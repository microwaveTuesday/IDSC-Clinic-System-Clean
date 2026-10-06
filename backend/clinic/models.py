"""
Clinic-owned database models for the IDSC Clinic System.

Domain ownership:
- Registrar owns student identity and profile data.
- Inventory owns medicines, stock, and inventory transactions.
- Clinic stores only Clinic-owned medical data.

External identifiers such as student_id and medicine_id are stored as
opaque string references. They are intentionally not database foreign keys.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class BloodTypeChoices(models.TextChoices):
    A_POSITIVE = "A+", "A+"
    A_NEGATIVE = "A-", "A-"
    B_POSITIVE = "B+", "B+"
    B_NEGATIVE = "B-", "B-"
    AB_POSITIVE = "AB+", "AB+"
    AB_NEGATIVE = "AB-", "AB-"
    O_POSITIVE = "O+", "O+"
    O_NEGATIVE = "O-", "O-"
    UNKNOWN = "Unknown", "Unknown"


class HealthStatusChoices(models.TextChoices):
    CLEARED = "CLEARED", "Cleared"
    RESTRICTED = "RESTRICTED", "Restricted"
    UNDER_OBSERVATION = "UNDER_OBSERVATION", "Under Observation"


class DispensationStatusChoices(models.TextChoices):
    COMPLETED = "COMPLETED", "Completed"
    ROLLED_BACK = "ROLLED_BACK", "Rolled Back"


class HealthRecord(models.Model):
    """
    Persistent Clinic-owned medical information for a student.

    student_id references a student owned by Registrar. It is deliberately
    stored as a string rather than a foreign key because Clinic does not own
    the Student entity.
    """

    health_record_id = models.BigAutoField(primary_key=True)

    student_id = models.CharField(
        max_length=100,
        db_index=True,
            #Temporarily allow null for testing purposes; should be non-null in production
        help_text="Opaque student identifier owned by Registrar",
    )

    blood_type = models.CharField(
        max_length=10,
        choices=BloodTypeChoices.choices,
        blank=True,
        default="",
    )

    allergies = models.TextField(
        blank=True,
        default="",
    )

    medical_history = models.TextField(
        blank=True,
        default="",
    )

    current_medications = models.TextField(
        blank=True,
        default="",
    )

    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "health_records"
        ordering = ["-created_at", "-health_record_id"]
        indexes = [
            models.Index(
                fields=["student_id", "-created_at"],
                name="idx_hr_student_created",
            ),
        ]

    def __str__(self):
        return f"HealthRecord #{self.health_record_id} - {self.student_id}"


class Consultation(models.Model):
    """Clinic visit or consultation associated with a Registrar student."""

    consultation_id = models.BigAutoField(primary_key=True)

    student_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Opaque student identifier owned by Registrar",
    )

    chief_complaint = models.TextField()
    assessment = models.TextField(blank=True, default="")
    treatment = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")

    consulted_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "consultations"
        ordering = ["-consulted_at", "-consultation_id"]
        indexes = [
            models.Index(
                fields=["student_id", "-consulted_at"],
                name="idx_cons_student_date",
            ),
        ]

    def __str__(self):
        return f"Consultation #{self.consultation_id} - {self.student_id}"


class HealthStatus(models.Model):
    """
    Current/historical health-status assessment owned by Clinic.

    NOT_AVAILABLE is intentionally not a database choice. It is an integration
    response state used when a student exists but Clinic has no stored status.
    """

    status_id = models.BigAutoField(primary_key=True)

    student_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Opaque student identifier owned by Registrar",
    )

    status = models.CharField(
        max_length=32,
        choices=HealthStatusChoices.choices,
    )

    remarks = models.TextField(blank=True, default="")

    effective_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "health_statuses"
        ordering = ["-effective_at", "-status_id"]
        indexes = [
            models.Index(
                fields=["student_id", "-effective_at"],
                name="idx_hs_student_effect",
            ),
            models.Index(
                fields=["status"],
                name="idx_hs_status",
            ),
        ]

    def __str__(self):
        return f"HealthStatus #{self.status_id} - {self.student_id}: {self.status}"


class MedicineDispensation(models.Model):
    """
    Clinic-owned record of medicine dispensed to a student.

    Medicine catalog and stock remain owned by Inventory. Clinic stores the
    external medicine identifier and Inventory transaction references required
    for auditability and rollback.
    """

    dispensation_id = models.BigAutoField(primary_key=True)

    student_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Opaque student identifier owned by Registrar",
    )

    medicine_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Opaque medicine identifier owned by Inventory",
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    reason = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=DispensationStatusChoices.choices,
        default=DispensationStatusChoices.COMPLETED,
    )

    inventory_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        db_index=True,
        help_text="Inventory transaction created when stock is deducted",
    )

    rollback_transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Inventory transaction created when a dispensation is rolled back",
    )

    dispensed_at = models.DateTimeField(auto_now_add=True)

    rolled_back_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "medicine_dispensations"
        ordering = ["-dispensed_at", "-dispensation_id"]
        indexes = [
            models.Index(
                fields=["student_id", "-dispensed_at"],
                name="idx_md_student_date",
            ),
            models.Index(
                fields=["medicine_id", "-dispensed_at"],
                name="idx_md_medicine_date",
            ),
            models.Index(
                fields=["status"],
                name="idx_md_status",
            ),
        ]

    def __str__(self):
        return (
            f"Dispensation #{self.dispensation_id} - "
            f"{self.student_id} / {self.medicine_id}"
        )