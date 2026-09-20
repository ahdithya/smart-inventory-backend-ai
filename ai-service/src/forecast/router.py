"""Router endpoint peramalan /forecast."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.auth import verify_api_key
from src.envelope import success
from src.forecast.schemas import ForecastRequest
from src.forecast.service import generate_demand_forecast

router = APIRouter(tags=["Forecast"])


@router.post("/forecast", dependencies=[Depends(verify_api_key)])
async def forecast_endpoint(payload: ForecastRequest) -> JSONResponse:
    """
    Menghitung prediksi permintaan 7 & 14 hari untuk produk tertentu
    menggunakan model statistik (Moving Average & Exponential Smoothing).
    Memerlukan header autentikasi X-API-Key.
    """
    forecast_data = generate_demand_forecast(payload)
    return success(data=forecast_data.model_dump(), message="Berhasil")
