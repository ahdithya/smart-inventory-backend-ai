"""Service integrasi peramalan permintaan antara Backend Django dan ai-service."""

import datetime
import logging
from typing import Any, Dict, List, Optional
import httpx
from django.conf import settings
from django.utils import timezone

from apps.products.models import Product
from apps.sales.services import get_daily_sales_history

from .models import Forecast

logger = logging.getLogger(__name__)

CACHE_WINDOW_HOURS = 6


def is_forecast_fresh(generated_at: datetime.datetime) -> bool:
    """Mengecek apakah peramalan masih segar (< 6 jam, sesuai BR-12)."""
    return (timezone.now() - generated_at) < datetime.timedelta(hours=CACHE_WINDOW_HOURS)


def format_forecast_response(
    product: Product,
    forecasts: List[Forecast],
    stale: bool = False,
    status_code: str = "OK",
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Format dictionary representasi peramalan produk."""
    horizons_data = []
    model_name = ""
    latest_gen_at = None

    for f in forecasts:
        if not model_name:
            model_name = f.model_name
        if latest_gen_at is None or f.generated_at > latest_gen_at:
            latest_gen_at = f.generated_at

        horizons_data.append(
            {
                "horizon_days": f.horizon_days,
                "total_predicted": f.total_predicted,
                "daily": f.daily_breakdown,
                "metrics": f.metrics,
            }
        )

    return {
        "product_id": product.id,
        "product_name": product.name,
        "product_sku": product.sku,
        "status": status_code,
        "message": message,
        "stale": stale,
        "model": model_name,
        "generated_at": latest_gen_at.isoformat() if latest_gen_at else None,
        "horizons": horizons_data,
    }


def get_or_generate_product_forecast(
    product: Product,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Mengambil atau menghasilkan peramalan untuk satu produk.
    1. Cek cache DB: jika ada data 7 & 14 hari dan masih segar (< 6 jam), kembalikan data DB.
    2. Jika kedaluwarsa atau tidak ada: panggil ai-service.
    3. Simpan hasil baru ke DB.
    4. Jika ai-service gagal (timeout/error): fallback ke data lama di DB dengan stale=True (BR-15).
    """
    existing_forecasts = list(Forecast.objects.filter(product=product).order_by("horizon_days"))

    # Cek apakah cache DB lengkap (horizon 7 & 14) dan masih segar (< 6 jam)
    has_both_horizons = len(existing_forecasts) >= 2
    is_fresh = has_both_horizons and all(is_forecast_fresh(f.generated_at) for f in existing_forecasts)

    if not force_refresh and is_fresh:
        return format_forecast_response(product, existing_forecasts, stale=False)

    # Ambil riwayat 90 hari
    sales_history = get_daily_sales_history(product.id, days=90)

    # Cek syarat minimal 30 hari data unik (BR-11)
    if len(sales_history) < 30:
        if existing_forecasts:
            return format_forecast_response(
                product,
                existing_forecasts,
                stale=True,
                status_code="INSUFFICIENT_DATA",
                message="Riwayat penjualan terbaru kurang dari 30 hari. Menampilkan data peramalan sebelumnya.",
            )
        return {
            "product_id": product.id,
            "product_name": product.name,
            "product_sku": product.sku,
            "status": "INSUFFICIENT_DATA",
            "message": "Riwayat penjualan kurang dari 30 hari (belum cukup untuk peramalan).",
            "stale": False,
            "model": None,
            "generated_at": None,
            "horizons": [],
        }

    # Panggil ai-service
    payload = {
        "product_id": product.id,
        "sales_history": sales_history,
        "horizon_days": [7, 14],
        "model": "auto",
    }

    url = f"{settings.AI_SERVICE_URL.rstrip('/')}/forecast"
    headers = {"X-API-Key": settings.AI_SERVICE_API_KEY}

    try:
        with httpx.Client(timeout=settings.AI_SERVICE_TIMEOUT) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            res_json = response.json()
            data = res_json.get("data", {})
            model_name = data.get("model", "auto")
            horizons_resp = data.get("horizons", [])
            now = timezone.now()

            saved_forecasts = []
            for h in horizons_resp:
                f_obj, _ = Forecast.objects.update_or_create(
                    product=product,
                    horizon_days=h["horizon_days"],
                    defaults={
                        "generated_at": now,
                        "total_predicted": int(round(h.get("total_predicted", 0))),
                        "daily_breakdown": h.get("daily", []),
                        "model_name": model_name,
                        "metrics": h.get("metrics", {}),
                    },
                )
                saved_forecasts.append(f_obj)

            return format_forecast_response(product, saved_forecasts, stale=False)

        elif response.status_code == 400 and response.json().get("code") == "INSUFFICIENT_DATA":
            if existing_forecasts:
                return format_forecast_response(
                    product,
                    existing_forecasts,
                    stale=True,
                    status_code="INSUFFICIENT_DATA",
                    message="Riwayat penjualan kurang dari 30 hari.",
                )
            return {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "status": "INSUFFICIENT_DATA",
                "message": "Riwayat penjualan kurang dari 30 hari.",
                "stale": False,
                "model": None,
                "generated_at": None,
                "horizons": [],
            }
        else:
            logger.warning(
                "ai-service mengembalikan status error %s untuk produk %s",
                response.status_code,
                product.id,
            )
            # Fallback ke cache jika ada
            if existing_forecasts:
                return format_forecast_response(
                    product,
                    existing_forecasts,
                    stale=True,
                    message="ai-service mengembalikan respons tidak terduga; menggunakan data cache.",
                )
            return {
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "status": "AI_SERVICE_ERROR",
                "message": f"ai-service error: {response.text}",
                "stale": False,
                "model": None,
                "generated_at": None,
                "horizons": [],
            }

    except (httpx.RequestError, httpx.TimeoutException) as exc:
        logger.warning(
            "Gagal menghubungi ai-service (%s). Menggunakan fallback untuk produk %s.",
            exc,
            product.id,
        )
        if existing_forecasts:
            return format_forecast_response(
                product,
                existing_forecasts,
                stale=True,
                message="ai-service tidak tersedia; menggunakan data peramalan terakhir.",
            )
        return {
            "product_id": product.id,
            "product_name": product.name,
            "product_sku": product.sku,
            "status": "SERVICE_UNAVAILABLE",
            "message": "ai-service sedang tidak dapat dijangkau dan belum ada data peramalan sebelumnya.",
            "stale": False,
            "model": None,
            "generated_at": None,
            "horizons": [],
        }
