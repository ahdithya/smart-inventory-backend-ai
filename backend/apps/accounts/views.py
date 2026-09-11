from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from shared.envelope import APIResponse

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
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
