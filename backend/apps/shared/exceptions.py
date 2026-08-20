from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response


class APIException(drf_exceptions.APIException):
    """Base exception custom dengan `code` standar (UPPER_SNAKE)."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "ERROR"
    message = "Terjadi kesalahan."

    def __init__(self, message=None, code=None, status_code=None):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.detail = self.message
        super().__init__(self.detail)


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"
    message = "Sumber daya tidak ditemukan."


class BusinessError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BUSINESS_ERROR"
    message = "Operasi tidak dapat dilakukan."


_CODE_MAP = {
    drf_exceptions.AuthenticationFailed: "UNAUTHENTICATED",
    drf_exceptions.NotAuthenticated: "UNAUTHENTICATED",
    drf_exceptions.PermissionDenied: "FORBIDDEN",
    drf_exceptions.NotFound: "NOT_FOUND",
    drf_exceptions.MethodNotAllowed: "METHOD_NOT_ALLOWED",
    drf_exceptions.ParseError: "PARSE_ERROR",
    drf_exceptions.UnsupportedMediaType: "UNSUPPORTED_MEDIA_TYPE",
    drf_exceptions.Throttled: "THROTTLED",
}


def _error(code, message, status_code, fields=None):
    payload = {"status": "error", "code": code, "message": message}
    if fields is not None:
        payload["fields"] = fields
    return Response(payload, status=status_code)


def api_exception_handler(exc, context):
    if isinstance(exc, APIException):
        return _error(exc.code, exc.message, exc.status_code)

    if isinstance(exc, Http404):
        return _error(
            "NOT_FOUND", "Sumber daya tidak ditemukan.", status.HTTP_404_NOT_FOUND
        )
    if isinstance(exc, DjangoPermissionDenied):
        return _error(
            "FORBIDDEN",
            "Anda tidak memiliki izin untuk aksi ini.",
            status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, drf_exceptions.ValidationError):
        fields = exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
        return _error(
            "VALIDATION_ERROR",
            "Terjadi kesalahan pada input.",
            status.HTTP_400_BAD_REQUEST,
            fields=fields,
        )

    if isinstance(exc, drf_exceptions.APIException):
        code = _CODE_MAP.get(
            type(exc), getattr(exc, "default_code", "ERROR") or "ERROR"
        )
        code = str(code).upper()
        message = exc.detail if isinstance(exc.detail, str) else str(exc.default_detail)
        return _error(code, message, exc.status_code)

    return _error(
        "INTERNAL_ERROR",
        "Terjadi kesalahan pada server.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
