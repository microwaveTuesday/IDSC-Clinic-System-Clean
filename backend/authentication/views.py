from rest_framework.decorators import throttle_classes
from .throttles import LoginThrottle
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_post_parameters
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect

from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from rest_framework.exceptions import ValidationError


from .permissions import IsClinicAdmin, IsOwner
from .pagination import StaffPagination
from .serializers import (
    CLINIC_STAFF,
    ClinicUserSerializer,
    CsrfTokenResponseSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    MessageResponseSerializer,
    PasswordChangeRequestSerializer,
    UsernameChangeRequestSerializer,
    AdminCreateSerializer,
    CLINIC_ADMIN,
    AdminAccountSerializer,
    AccountDeleteRequestSerializer,
    SessionUserSerializer,
    StaffCreateSerializer,
    ManagedAccountUpdateSerializer,
)
from .account_lifecycle import change_account_access


@extend_schema(
    responses=CsrfTokenResponseSerializer,
)
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_token(request):
    """
    Return a CSRF token and ensure the CSRF cookie is set.
    """
    token = get_token(request)

    return Response({"csrfToken": token})


@extend_schema(
    request=LoginRequestSerializer,
    responses=LoginResponseSerializer,
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
@throttle_classes([LoginThrottle])
def login_view(request):
    """
    Authenticate a user and create a Django session.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = LoginRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request,
        **serializer.validated_data,
    )

    if user is None:
        return Response(
            {"detail": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    login(request, user)

    return Response(
        {
            "message": "Login successful.",
            "user": SessionUserSerializer(user).data,
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(
    request=None,
    responses=MessageResponseSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Log out the current authenticated user and destroy the session.
    """
    logout(request)

    return Response(
        {"message": "Logout successful."},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    responses=SessionUserSerializer,
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Return information about the currently authenticated user.
    """
    user = request.user

    return Response(
        SessionUserSerializer(user).data,
        status=status.HTTP_200_OK,
    )


@sensitive_post_parameters("current_password", "new_password", "confirm_password")
@extend_schema(
    request=PasswordChangeRequestSerializer,
    responses={200: MessageResponseSerializer},
    summary="Change your password",
    description=(
        "Change the authenticated user's password after verifying the current password. "
        "Requires a session cookie and X-CSRFToken. Django password validators apply. "
        "The current session is rotated and retained; other sessions expire on their next request."
    ),
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def password_change_view(request):
    # Re-read and lock this account so validation uses its latest password.
    with transaction.atomic():
        user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
        serializer = PasswordChangeRequestSerializer(
            data=request.data, context={"user": user}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
    update_session_auth_hash(request, user)
    return Response({"message": "Your password has been changed."})


User = get_user_model()


@sensitive_post_parameters("current_password")
@extend_schema(
    request=UsernameChangeRequestSerializer,
    responses={200: SessionUserSerializer},
    summary="Change your username",
    description="Change only the signed-in user's username after current-password verification. Requires session authentication and CSRF. The current session is retained; future logins use the new username.",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def username_change_view(request):
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            serializer = UsernameChangeRequestSerializer(
                data=request.data, context={"user": user}
            )
            serializer.is_valid(raise_exception=True)
            user.username = serializer.validated_data["new_username"]
            user.save(update_fields=["username"])
    except IntegrityError as exc:
        raise ValidationError(
            {"new_username": "This username is already in use."}
        ) from exc
    return Response(SessionUserSerializer(user).data)


class AdminListCreateView(ListCreateAPIView):
    permission_classes = [IsOwner]
    pagination_class = None

    def get_queryset(self):
        return (
            User.objects.filter(groups__name=CLINIC_ADMIN, is_superuser=False)
            .distinct()
            .order_by("username")
        )

    def get_serializer_class(self):
        return (
            AdminCreateSerializer
            if self.request.method == "POST"
            else AdminAccountSerializer
        )

    @extend_schema(
        request=AdminCreateSerializer,
        responses={
            201: ClinicUserSerializer,
            409: OpenApiResponse(
                description="Maximum 5 administrators, including inactive accounts. Delete an administrator to free a slot."
            ),
        },
        description="Owner only. Maximum five regular administrators, including inactive accounts; owners do not count. At capacity returns 409. Requires owner current password, CSRF and a validated new password.",
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ClinicUserSerializer(user).data, status=status.HTTP_201_CREATED)


class StaffListView(ListCreateAPIView):
    pagination_class = StaffPagination
    serializer_class = ClinicUserSerializer
    permission_classes = [IsClinicAdmin]

    def get_queryset(self):
        return (
            User.objects.filter(groups__name=CLINIC_STAFF, is_superuser=False)
            .exclude(groups__name=CLINIC_ADMIN)
            .order_by("username")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StaffCreateSerializer

        return ClinicUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        response_serializer = ClinicUserSerializer(
            user,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    put=extend_schema(
        request=ManagedAccountUpdateSerializer, responses=ClinicUserSerializer
    ),
    patch=extend_schema(
        request=ManagedAccountUpdateSerializer, responses=ClinicUserSerializer
    ),
)
class StaffDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsClinicAdmin]
    lookup_url_kwarg = "user_id"

    def get_queryset(self):
        return User.objects.filter(
            groups__name=CLINIC_STAFF, is_superuser=False
        ).exclude(groups__name=CLINIC_ADMIN)

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ManagedAccountUpdateSerializer

        return ClinicUserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_serializer = ClinicUserSerializer(
            user,
            context=self.get_serializer_context(),
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=AccountDeleteRequestSerializer, responses={204: None})
    def delete(self, request, user_id):
        change_account_access(request.user, user_id, "staff", "delete", request.data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StaffDeactivateView(APIView):
    permission_classes = [IsClinicAdmin]

    @extend_schema(
        request=None,
        responses=ClinicUserSerializer,
    )
    def post(self, request, user_id):
        user = change_account_access(request.user, user_id, "staff", "deactivate")

        return Response(
            ClinicUserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


class StaffActivateView(APIView):
    permission_classes = [IsClinicAdmin]

    @extend_schema(
        request=None,
        responses=ClinicUserSerializer,
    )
    def post(self, request, user_id):
        user = change_account_access(request.user, user_id, "staff", "activate")

        return Response(
            ClinicUserSerializer(user).data,
            status=status.HTTP_200_OK,
        )


class AdminDetailView(StaffDetailView):
    permission_classes = [IsOwner]

    def get_queryset(self):
        return User.objects.filter(groups__name=CLINIC_ADMIN, is_superuser=False)

    def get_serializer_class(self):
        return (
            ManagedAccountUpdateSerializer
            if self.request.method in ("PUT", "PATCH")
            else AdminAccountSerializer
        )

    @extend_schema(request=AccountDeleteRequestSerializer, responses={204: None})
    def delete(self, request, user_id):
        change_account_access(request.user, user_id, "admin", "delete", request.data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminAccessView(APIView):
    permission_classes = [IsOwner]
    action = None

    @extend_schema(request=None, responses=AdminAccountSerializer)
    def post(self, request, user_id):
        user = change_account_access(request.user, user_id, "admin", self.action)
        return Response(AdminAccountSerializer(user, context={"request": request}).data)


from .models import OwnerRegistration
from .owner_setup import registration_available
from .serializers import OwnerRegisterSerializer, OwnerSetupStatusSerializer
from clinic.exceptions import ConflictError


@extend_schema(
    responses=OwnerSetupStatusSerializer,
    description="Public first-run status only. Inactive or previously registered Owners keep registration closed.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def owner_setup_status(request):
    response = Response({"owner_registration_available": registration_available()})
    response["Cache-Control"] = "no-store"
    return response


@sensitive_post_parameters("password", "confirm_password")
@extend_schema(
    request=OwnerRegisterSerializer,
    responses={
        201: LoginResponseSerializer,
        409: OpenApiResponse(description="Owner registration is already complete."),
    },
    description="One-time first Owner registration. Requires CSRF even without a session. Creates exactly one Owner, starts a Django session, and permanently closes registration.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
def owner_register(request):
    # Check before validation to avoid offering a usable registration endpoint once claimed.
    if not registration_available():
        raise ConflictError("Owner registration is already complete. Please log in.")
    serializer = OwnerRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        with transaction.atomic():
            # First acquire a write lock, including on SQLite, before checking availability.
            changed = OwnerRegistration.objects.filter(pk=1).update(id=1)
            if not changed:
                OwnerRegistration.objects.create(pk=1)
            state = OwnerRegistration.objects.select_for_update().get(pk=1)
            if state.owner_id is not None or not registration_available():
                raise ConflictError(
                    "Owner registration is already complete. Please log in."
                )
            data = dict(serializer.validated_data)
            data.pop("confirm_password")
            user = User.objects.create_superuser(**data)
            state.owner = user
            state.save(update_fields=["owner"])
    except IntegrityError as exc:
        raise ConflictError(
            "Owner registration is no longer available or the username is already in use. Please reload."
        ) from exc
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    response = Response(
        {"message": "Owner account created.", "user": SessionUserSerializer(user).data},
        status=201,
    )
    response["Cache-Control"] = "no-store"
    return response
