"""Skema Pydantic untuk endpoint peramalan /forecast."""

from datetime import date
from typing import List, Literal, Union
from pydantic import BaseModel, Field


class SalesHistoryItem(BaseModel):
    """Satu entri riwayat penjualan harian produk."""

    date: Union[date, str]
    qty: float = Field(ge=0, description="Kuantitas terjual harian (harus non-negatif)")


class ForecastRequest(BaseModel):
    """Payload permintaan peramalan dari backend ke ai-service."""

    product_id: int
    sales_history: List[SalesHistoryItem]
    horizon_days: List[int] = Field(default=[7, 14], description="Daftar horizon hari peramalan")
    model: Literal[
        "moving_average", "exponential_smoothing", "auto", "pretrained", "champion"
    ] = Field(
        default="auto",
        description="Model peramalan yang digunakan"
    )


class DailyForecast(BaseModel):
    """Hasil peramalan untuk satu hari tertentu."""

    date: str
    qty: float


class MetricsResult(BaseModel):
    """Metrik evaluasi akurasi peramalan terhadap data validasi."""

    mae: float
    rmse: float
    mape: float
    wape: float


class HorizonResult(BaseModel):
    """Hasil peramalan untuk satu horizon tertentu (misal 7 atau 14 hari)."""

    horizon_days: int
    total_predicted: float
    daily: List[DailyForecast]
    metrics: MetricsResult


class ForecastData(BaseModel):
    """Payload data peramalan lengkap dalam envelope respons sukses."""

    product_id: int
    horizons: List[HorizonResult]
    model: str
    generated_at: str
