from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from clinic.exceptions import ConflictError
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

User = get_user_model()

CLINIC_ADMIN = "CLINIC_ADMIN"
CLINIC_STAFF = "CLINIC_STAFF"

ROLE_OWNER = "OWNER"
ROLE_ADMIN = "ADMIN"
ROLE_STAFF = "STAFF"


# ---------------------------------------------------------------------------
# Authentication/session API schema serializers
# ---------------------------------------------------------------------------


class CsrfTokenResponseSerializer(serializers.Serializer):
    csrfToken = serializers.CharField(read_only=True)


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )


class PasswordChangeRequestSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    new_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    confirm_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )

    def validate(self, attrs):
        user = self.context["user"]
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Your current password is incorrect."}
            )
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The new passwords do not match."}
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": "Choose a different password from your current password."
                }
            )
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages}) from exc
        return attrs


class SessionUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(
        read_only=True,
        allow_blank=True,
    )
    is_staff = serializers.BooleanField(read_only=True)
    role = serializers.SerializerMethodField()

    @extend_schema_field(
        serializers.ChoiceField(
            choices=[ROLE_OWNER, ROLE_ADMIN, ROLE_STAFF], allow_null=True
        )
    )
    def get_role(self, obj) -> str | None:
        return get_user_role(obj)


def validate_available_username(value, exclude_id=None):
    value = User.normalize_username(value.strip())
    try:
        User._meta.get_field("username").clean(value, None)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages) from exc
    if User.objects.filter(username__iexact=value).exclude(pk=exclude_id).exists():
        raise serializers.ValidationError("This username is already in use.")
    return value


class UsernameChangeRequestSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    new_username = serializers.CharField(max_length=150)

    def validate_new_username(self, value):
        user = self.context["user"]
        value = validate_available_username(value, exclude_id=user.pk)
        if value == user.username:
            raise serializers.ValidationError("Choose a different username.")
        return value

    def validate(self, attrs):
        if not self.context["user"].check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Your current password is incorrect."}
            )
        return attrs


class AccountDeleteRequestSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )

    def validate_current_password(self, value):
        if not self.context["user"].check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)
    user = SessionUserSerializer(read_only=True)


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)


def get_user_role(user):
    if user.is_superuser:
        return ROLE_OWNER

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

    @extend_schema_field(
        serializers.ChoiceField(
            choices=[ROLE_OWNER, ROLE_ADMIN, ROLE_STAFF], allow_null=True
        )
    )
    def get_role(self, obj) -> str | None:
        return get_user_role(obj)


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        trim_whitespace=False,
        max_length=1024,
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
            raise serializers.ValidationError("Username is required.")

        return value

    def validate(self, attrs):
        candidate = User(**{k: v for k, v in attrs.items() if k != "password"})
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.is_active = True
        user.set_password(password)
        user.save()

        staff_group = Group.objects.get(name=CLINIC_STAFF)
        user.groups.add(staff_group)

        return user


class AdminAccountSerializer(ClinicUserSerializer):
    is_system_admin = serializers.BooleanField(source="is_superuser", read_only=True)
    can_manage = serializers.SerializerMethodField()
    management_restriction = serializers.SerializerMethodField()

    class Meta(ClinicUserSerializer.Meta):
        fields = ClinicUserSerializer.Meta.fields + [
            "is_system_admin",
            "can_manage",
            "management_restriction",
        ]

    def get_management_restriction(self, obj) -> str:
        actor = self.context["request"].user
        if obj.is_superuser:
            return "Owner accounts cannot be managed here."
        if actor.pk == obj.pk:
            return "You cannot deactivate or delete your own account."
        if not actor.is_superuser:
            return "Only the owner can manage administrator accounts."
        return ""

    def get_can_manage(self, obj) -> bool:
        return not self.get_management_restriction(obj)


class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]


class ManagedAccountUpdateSerializer(StaffUpdateSerializer):
    username = serializers.CharField(max_length=150, required=False)

    class Meta(StaffUpdateSerializer.Meta):
        fields = ["username", "first_name", "last_name", "email"]

    def validate_username(self, value):
        return validate_available_username(value, exclude_id=self.instance.pk)

    def validate(self, attrs):
        forbidden = {
            "role",
            "groups",
            "is_superuser",
            "is_staff",
            "is_active",
            "password",
        } & self.initial_data.keys()
        if forbidden:
            raise serializers.ValidationError(
                "Account edits cannot change roles, access, or passwords. Use the dedicated access actions."
            )
        return attrs


class AdminCreateSerializer(StaffCreateSerializer):
    current_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    confirm_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )

    class Meta(StaffCreateSerializer.Meta):
        fields = StaffCreateSerializer.Meta.fields + [
            "current_password",
            "confirm_password",
        ]

    def validate_username(self, value):
        return validate_available_username(value)

    def validate(self, attrs):
        if not self.context["request"].user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Your current password is incorrect."}
            )
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The new administrator passwords do not match."}
            )
        candidate = User(
            **{
                key: value
                for key, value in attrs.items()
                if key not in {"password", "current_password", "confirm_password"}
            }
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Serialize the capacity check across all owner sessions on the shared role row.
        # Acquire a write lock before reading capacity on SQLite too (which ignores
        # SELECT FOR UPDATE). The role name does not change.
        Group.objects.filter(name=CLINIC_ADMIN).update(name=CLINIC_ADMIN)
        admin_group = Group.objects.select_for_update().get(name=CLINIC_ADMIN)
        if User.objects.filter(groups=admin_group, is_superuser=False).count() >= 5:
            raise ConflictError(
                "The maximum of 5 administrator accounts has been reached. Delete an administrator before adding a new one. Inactive administrators also count."
            )
        validated_data.pop("current_password")
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        # Clinic administration is an application role, never Django superuser access.
        user = User(
            **validated_data, is_active=True, is_staff=False, is_superuser=False
        )
        user.set_password(password)
        user.save()
        user.groups.add(admin_group)
        return user


class OwnerSetupStatusSerializer(serializers.Serializer):
    owner_registration_available = serializers.BooleanField(read_only=True)


class OwnerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )
    confirm_password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=1024
    )

    def validate_username(self, value):
        return validate_available_username(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "The passwords do not match."}
            )
        candidate = User(
            **{
                key: value
                for key, value in attrs.items()
                if key not in {"password", "confirm_password"}
            }
        )
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs
