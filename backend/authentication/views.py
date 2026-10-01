from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect

from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView



from .permissions import IsClinicAdmin
from .serializers import (
    ClinicUserSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer,
    CLINIC_STAFF,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf_token(request):
    """
    Return a CSRF token and ensure the CSRF cookie is set.
    """
    token = get_token(request)

    return Response({
        "csrfToken": token
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_protect
def login_view(request):
    """
    Authenticate a user and create a Django session.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {
                "detail": "Username and password are required."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {
                "detail": "Invalid username or password."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {
                "detail": "This account is inactive."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    login(request, user)

    return Response(
        {
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Log out the current authenticated user and destroy the session.
    """
    logout(request)

    return Response(
        {
            "message": "Logout successful."
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Return information about the currently authenticated user.
    """
    user = request.user

    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
        },
        status=status.HTTP_200_OK,
    )

User = get_user_model()


class StaffListView(ListCreateAPIView):
    serializer_class = ClinicUserSerializer
    permission_classes = [IsClinicAdmin]

    def get_queryset(self):
        return (
            User.objects
            .filter(groups__name=CLINIC_STAFF)
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

class StaffDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsClinicAdmin]
    lookup_url_kwarg = "user_id"

    def get_queryset(self):
        return User.objects.filter(
            groups__name=CLINIC_STAFF
        )

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return StaffUpdateSerializer

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

class StaffDeactivateView(APIView):
    permission_classes = [IsClinicAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(
                id=user_id,
                groups__name=CLINIC_STAFF,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Staff account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {"detail": "Staff account is already inactive."},
                status=status.HTTP_409_CONFLICT,
            )

        user.is_active = False
        user.save(update_fields=["is_active"])

        return Response(
            ClinicUserSerializer(user).data,
            status=status.HTTP_200_OK,
        )

class StaffActivateView(APIView):
    permission_classes = [IsClinicAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(
                id=user_id,
                groups__name=CLINIC_STAFF,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "Staff account not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {"detail": "Staff account is already active."},
                status=status.HTTP_409_CONFLICT,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            ClinicUserSerializer(user).data,
            status=status.HTTP_200_OK,
        )
