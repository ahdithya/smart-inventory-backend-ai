from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from shared.envelope import APIResponse
from shared.exceptions import NotFoundError

from .models import BusinessProfile, User
from .permissions import IsOwner
from .serializers import (
    BusinessProfileSerializer,
    LoginSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
    get_tokens_for_user,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return APIResponse(
            data={
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": UserSerializer(user).data,
            },
            status_code=status.HTTP_201_CREATED,
            message="Registrasi berhasil",
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = get_tokens_for_user(serializer.validated_data["user"])
        return APIResponse(
            data=tokens,
            status_code=status.HTTP_200_OK,
            message="Login berhasil",
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ValidationError({"refresh": ["Refresh token wajib diisi."]})
        try:
            refresh = RefreshToken(refresh_token)
        except TokenError:
            raise AuthenticationFailed("Refresh token tidak valid atau kedaluwarsa.")
        return APIResponse(
            data={"access": str(refresh.access_token)},
            status_code=status.HTTP_200_OK,
            message="Token berhasil diperbarui",
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return APIResponse(
            data=UserSerializer(request.user).data,
            status_code=status.HTTP_200_OK,
            message="Profil berhasil diambil",
        )


class BusinessProfileView(APIView):
    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsOwner()]
        return [IsAuthenticated()]

    def get(self, request):
        profile = BusinessProfile.objects.first()
        if profile is None:
            raise NotFoundError("Profil bisnis belum tersedia.")
        return APIResponse(
            data=BusinessProfileSerializer(profile).data,
            status_code=status.HTTP_200_OK,
            message="Profil bisnis berhasil diambil",
        )

    def put(self, request):
        profile = request.user.business_profile
        serializer = BusinessProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Profil bisnis berhasil diperbarui",
        )


class UserListView(APIView):
    permission_classes = [IsOwner]

    def get(self, request):
        users = User.objects.all().order_by("id")
        return APIResponse(
            data={"users": UserSerializer(users, many=True).data},
            status_code=status.HTTP_200_OK,
            message="Daftar user berhasil diambil",
        )

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return APIResponse(
            data=UserSerializer(user).data,
            status_code=status.HTTP_201_CREATED,
            message="User berhasil dibuat",
        )


class UserRoleUpdateView(APIView):
    permission_classes = [IsOwner]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise NotFoundError("User tidak ditemukan.")
        serializer = RoleUpdateSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=UserSerializer(user).data,
            status_code=status.HTTP_200_OK,
            message="Role user berhasil diubah",
        )
