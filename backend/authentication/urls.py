from django.urls import path

from .views import (
    csrf_token,
    owner_setup_status,
    owner_register,
    login_view,
    logout_view,
    me_view,
    password_change_view,
    username_change_view,
)


urlpatterns = [
    path("setup/", owner_setup_status, name="owner-setup-status"),
    path("owner/register/", owner_register, name="owner-register"),
    path("csrf/", csrf_token, name="csrf-token"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("me/", me_view, name="me"),
    path("password/change/", password_change_view, name="password-change"),
    path("username/change/", username_change_view, name="username-change"),
]
