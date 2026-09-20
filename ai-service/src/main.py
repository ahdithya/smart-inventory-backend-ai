"""Aplikasi FastAPI untuk ai-service."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth import APIKeyAuthError
from src.envelope import error
from src.forecast.router import router as forecast_router
from src.forecast.service import InsufficientDataError

app = FastAPI(
    title="Smartify UMKM - AI Service",
    description="Stateless microservice untuk demand forecasting & rekomendasi restock.",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(APIKeyAuthError)
async def auth_exception_handler(request: Request, exc: APIKeyAuthError) -> JSONResponse:
    """Tangani error autentikasi API Key dengan envelope standar."""
    return error(code=exc.code, message=exc.message, status_code=exc.status_code)


@app.exception_handler(InsufficientDataError)
async def insufficient_data_exception_handler(request: Request, exc: InsufficientDataError) -> JSONResponse:
    """Tangani error riwayat penjualan kurang dari 30 hari (HTTP 400)."""
    return error(code=exc.code, message=exc.message, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Tangani error validasi input dengan envelope standar."""
    return error(
        code="VALIDATION_ERROR",
        message=f"Terjadi kesalahan validasi input: {exc.errors()}",
        status_code=422,
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint pemeriksaan kesehatan service. Bebas autentikasi sesuai kontrak §2.3."""
    return {"status": "ok"}


# Registrasi router fitur peramalan
app.include_router(forecast_router)


if __name__ == "__main__":
    import uvicorn
    from src.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.ai_service_port,
        reload=True,
    )
