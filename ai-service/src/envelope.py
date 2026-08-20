"""Helper envelope respons standar untuk ai-service (lihat docs/ARCHITECTURE.md §2.3)."""

from fastapi.responses import JSONResponse


def success(data, status_code: int = 200, message: str = "Berhasil") -> JSONResponse:
    """Buat {'status': 'success', 'message': ..., 'data': ...}."""
    return JSONResponse(
        status_code=status_code,
        content={"status": "success", "message": message, "data": data},
    )


def error(code: str, message: str, status_code: int = 400) -> JSONResponse:
    """Buat {'status': 'error', 'code': ..., 'message': ...}."""
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "code": code, "message": message},
    )
