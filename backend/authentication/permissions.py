from rest_framework.permissions import BasePermission

from .serializers import CLINIC_ADMIN, CLINIC_STAFF

class IsClinicAdmin(BasePermission):
    message = "Clinic administrator access is required."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(name=CLINIC_ADMIN).exists()

class IsClinicStaff(BasePermission):
    message = "Clinic staff access is required."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        if user.is_superuser:
            return True

        return user.groups.filter(
            name__in=[CLINIC_ADMIN, CLINIC_STAFF]
        ).exists()


class IsOwner(BasePermission):
    message = "Website owner access is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and user.is_superuser)
