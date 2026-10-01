from django.urls import path

from .views import (
    StaffActivateView,
    StaffDeactivateView,
    StaffDetailView,
    StaffListView,
)


urlpatterns = [
    path("", StaffListView.as_view(), name="staff-list"),
    path(
        "<int:user_id>/",
        StaffDetailView.as_view(),
        name="staff-detail"
    ),
    path(
        "<int:user_id>/deactivate/",
        StaffDeactivateView.as_view(),
        name="staff-deactivate",
    ),
    path(
        "<int:user_id>/activate/",
        StaffActivateView.as_view(),
        name="staff-activate",
    ),
]