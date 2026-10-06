from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers


User = get_user_model()

CLINIC_ADMIN = "CLINIC_ADMIN"
CLINIC_STAFF = "CLINIC_STAFF"

ROLE_ADMIN = "ADMIN"
ROLE_STAFF = "STAFF"


# ---------------------------------------------------------------------------
# Authentication/session API schema serializers
# ---------------------------------------------------------------------------


class CsrfTokenResponseSerializer(serializers.Serializer):
    csrfToken = serializers.CharField(
        read_only=True
    )


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class SessionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(
        read_only=True
    )
    username = serializers.CharField(
        read_only=True
    )
    email = serializers.EmailField(
        read_only=True,
        allow_blank=True,
    )
    is_staff = serializers.BooleanField(
        read_only=True
    )


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        read_only=True
    )
    user = SessionUserSerializer(
        read_only=True
    )


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        read_only=True
    )


def get_user_role(user):
    if user.is_superuser:
        return ROLE_ADMIN

    if user.groups.filter(name=CLINIC_ADMIN).exists():
        return ROLE_ADMIN

    if user.groups.filter(name=CLINIC_STAFF).exists():
        return ROLE_STAFF

    return None


class ClinicUserSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="id", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "is_active",
        ]
        read_only_fields = [
            "user_id",
            "role",
            "is_active",
        ]

    def get_role(self, obj) -> str | None:
        return get_user_role(obj)


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        ]

    def validate_username(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Username is required."
            )

        return value

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError(
                "Password is required."
            )

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.is_active = True
        user.set_password(password)
        user.save()

        staff_group = Group.objects.get(name=CLINIC_STAFF)
        user.groups.add(staff_group)

        return user


class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]