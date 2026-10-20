"""Remove expired response bodies while retaining duplicate-operation tombstones."""
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from clinic.models import OperationReceipt


class Command(BaseCommand):
    help = "Purge expired sensitive replay bodies; preserve keys, clinical history and audit."

    def handle(self, **options):
        cutoff = timezone.now() - timedelta(hours=settings.REPLAY_RETENTION_HOURS)
        count = OperationReceipt.objects.filter(created_at__lt=cutoff).exclude(response=None).update(response=None)
        self.stdout.write(f"Purged {count} expired replay bodies; operation tombstones retained.")
