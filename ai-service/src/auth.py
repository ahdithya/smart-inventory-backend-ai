"""Modul autentikasi header X-API-Key untuk ai-service."""

import secrets
from fastapi import Security
from fastapi.security import APIKeyHeader
from src.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyAuthError(Exception):
    """Exception khusus kegagalan autentikasi API key."""

    def __init__(
        self,
        message: str = "API key tidak valid atau tidak disertakan.",
        code: str = "UNAUTHORIZED",
        status_code: int = 401,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Dependency untuk memverifikasi keabsahan header X-API-Key."""
    settings = get_settings()
    if not api_key or not secrets.compare_digest(api_key, settings.ai_service_api_key):
        raise APIKeyAuthError(
            code="UNAUTHORIZED",
            message="API key tidak valid atau tidak disertakan.",
            status_code=401,
        )
    return api_key
