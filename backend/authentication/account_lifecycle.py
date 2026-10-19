"""Account access changes with shared authorization and lockout safeguards."""
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from clinic.exceptions import ConflictError
from .serializers import CLINIC_ADMIN, CLINIC_STAFF, AccountDeleteRequestSerializer

User = get_user_model()


def administrator_query():
    return Q(is_superuser=True) | Q(groups__name=CLINIC_ADMIN)


def revoke_sessions(user_id):
    # The verified framework runtime uses Django's database session backend.
    keys = [session.session_key for session in Session.objects.filter(expire_date__gt=timezone.now()).iterator()
            if str(session.get_decoded().get("_auth_user_id")) == str(user_id)]
    Session.objects.filter(session_key__in=keys).delete()


@transaction.atomic
def change_account_access(actor, user_id, role, action, data=None):
    # Lock base User rows in a deterministic order (not a DISTINCT join, which
    # PostgreSQL cannot lock). All admin lifecycle operations use this lock set.
    admin_ids = User.objects.filter(administrator_query()).values("pk")
    admins = list(User.objects.select_for_update().filter(pk__in=admin_ids).order_by("pk"))
    current_actor = next((user for user in admins if user.pk == actor.pk), None)
    if current_actor is None or not current_actor.is_active:
        raise PermissionDenied("An active clinic administrator is required.")

    query = User.objects.select_for_update()
    if role == "admin":
        query = query.filter(pk__in=admin_ids)
    else:
        # Mixed-role admins cannot bypass the admin safeguards via staff routes.
        query = query.filter(groups__name=CLINIC_STAFF).exclude(pk__in=admin_ids)
    try:
        target = query.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise NotFound("Administrator account not found." if role == "admin" else "Staff account not found.") from exc

    if role == "admin" and not current_actor.is_superuser:
        raise PermissionDenied("Only the website owner can manage administrator accounts.")
    if target.pk == current_actor.pk:
        raise ConflictError("You cannot deactivate, delete, or change access to your own account here.")
    if target.is_superuser:
        raise PermissionDenied("Owner accounts cannot be deleted or deactivated through account management.")

    if action == "delete":
        serializer = AccountDeleteRequestSerializer(data=data or {}, context={"user": current_actor})
        serializer.is_valid(raise_exception=True)
        revoke_sessions(target.pk)
        target.delete()
        return None

    active = action == "activate"
    if target.is_active == active:
        raise ConflictError("Account is already active." if active else "Account is already inactive.")
    target.is_active = active
    target.save(update_fields=["is_active"])
    if not active:
        revoke_sessions(target.pk)
    return target
