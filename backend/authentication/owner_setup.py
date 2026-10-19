from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import OwnerRegistration

User = get_user_model()


def registration_available():
    return not OwnerRegistration.objects.filter(owner__isnull=False).exists() and not User.objects.filter(is_superuser=True).exists()


@receiver(pre_save, sender=User)
def protect_single_owner(sender, instance, raw=False, **kwargs):
    if raw:
        return
    registered = OwnerRegistration.objects.filter(pk=1).values_list('owner_id', flat=True).first()
    if instance.is_superuser:
        if not instance.is_active:
            raise ValidationError('The Owner account must remain active.')
        if (registered is not None and registered != instance.pk) or User.objects.filter(is_superuser=True).exclude(pk=instance.pk).exists():
            raise ValidationError('This installation already has an Owner. A second Owner is not allowed.')
    if instance.pk is not None and registered == instance.pk and (not instance.is_active or not instance.is_superuser):
        raise ValidationError('The registered Owner cannot be deactivated or demoted.')


@receiver(post_save, sender=User)
def remember_owner(sender, instance, raw=False, **kwargs):
    if not raw and instance.is_superuser:
        OwnerRegistration.objects.filter(pk=1, owner__isnull=True).update(owner=instance)
