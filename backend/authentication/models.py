from django.conf import settings
from django.db import models


class OwnerRegistration(models.Model):
    """A permanent first-run latch: registration never reopens after completion."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="owner_registration")

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="single_owner_registration_row")]
