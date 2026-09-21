from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import BusinessProfile, User


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = ["id", "business_name", "business_type", "address", "phone"]


class UserSerializer(serializers.ModelSerializer):
    business_profile = BusinessProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active", "business_profile"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    business_name = serializers.CharField(max_length=200)
    business_type = serializers.ChoiceField(
        choices=BusinessProfile.BusinessType.choices,
        default=BusinessProfile.BusinessType.OTHERS,
        required=False,
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username sudah digunakan.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email sudah digunakan.")
        return value

    def create(self, validated_data):
        is_first_user = not User.objects.exists()
        role = User.Role.OWNER if is_first_user else User.Role.STAFF

        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            role=role,
        )

        # Set sementara SEBELUM save agar signal post_save membuat
        # BusinessProfile dengan business_name/type yang benar.
        user._business_name = validated_data["business_name"]
        user._business_type = validated_data.get(
            "business_type", BusinessProfile.BusinessType.OTHERS
        )
        user.set_password(validated_data["password"])
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Username atau password salah.")
        attrs["user"] = user
        return attrs


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=User.Role.choices,
        default=User.Role.STAFF,
        required=False,
    )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username sudah digunakan.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email sudah digunakan.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", User.Role.STAFF),
        )


class RoleUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["role", "is_active"]
