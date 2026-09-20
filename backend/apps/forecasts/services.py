"""Service integrasi peramalan permintaan antara Backend Django dan ai-service."""

import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import httpx
from django.conf import settings
from django.db.models import Case, IntegerField, Value, When
from django.utils import timezone

from apps.products.models import Product
from apps.sales.services import get_daily_sales_history

from .models import Forecast, RestockRecommendation

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

            # Hitung & simpan rekomendasi restock otomatis setelah forecast tersimpan (Tiket 13)
            try:
                calculate_restock_recommendation_for_product(product)
            except Exception as exc:
                logger.warning(
                    "Gagal memperbarui rekomendasi restock untuk produk %s: %s",
                    product.id,
                    exc,
                )

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


def calculate_restock_recommendation_for_product(
    product: Product,
    avg_daily_demand: Optional[Decimal | float] = None,
) -> RestockRecommendation:
    """
    Menghitung rekomendasi kuantitas restock produk berdasarkan formula (PRD §4.6 & DATABASE §2.8):
    recommended_qty = max(0, (avg_daily_demand × lead_time_days) + safety_stock − current_stock)

    Status Urgensi:
    - critical: current_stock <= 0
    - warning:  current_stock <= min_stock (dan current_stock > 0)
    - ok:       current_stock > min_stock

    Format detail JSON:
    {
        "avg_daily_demand": 6.0,
        "lead_time_days": 7,
        "lead_time_demand": 42,
        "safety_stock": 5,
        "current_stock": 30,
        "formula": "max(0, (6.0 × 7) + 5 − 30) = 17"
    }
    """
    if avg_daily_demand is None:
        f7 = (
            Forecast.objects.filter(product=product, horizon_days=7)
            .order_by("-generated_at")
            .first()
        )
        if f7 and f7.horizon_days > 0:
            avg_daily_demand = Decimal(
                str(round(f7.total_predicted / f7.horizon_days, 2))
            )
        else:
            f14 = (
                Forecast.objects.filter(product=product, horizon_days=14)
                .order_by("-generated_at")
                .first()
            )
            if f14 and f14.horizon_days > 0:
                avg_daily_demand = Decimal(
                    str(round(f14.total_predicted / f14.horizon_days, 2))
                )
            else:
                avg_daily_demand = Decimal("0.00")
    else:
        avg_daily_demand = Decimal(str(round(float(avg_daily_demand), 2)))

    avg_float = float(avg_daily_demand)
    lead_time_days = int(product.lead_time_days)
    safety_stock = int(product.safety_stock)
    current_stock = int(product.current_stock)
    min_stock = int(product.min_stock)

    lead_time_demand = int(round(avg_float * lead_time_days))
    raw_qty = (avg_float * lead_time_days) + safety_stock - current_stock
    recommended_qty = max(0, int(round(raw_qty)))

    if current_stock <= 0:
        urgency_status = "critical"
    elif current_stock <= min_stock:
        urgency_status = "warning"
    else:
        urgency_status = "ok"

    avg_str = f"{avg_float:.1f}" if avg_float.is_integer() else f"{avg_float}"
    formula_str = (
        f"max(0, ({avg_str} × {lead_time_days}) + {safety_stock} − {current_stock}) = {recommended_qty}"
    )

    detail = {
        "avg_daily_demand": avg_float,
        "lead_time_days": lead_time_days,
        "lead_time_demand": lead_time_demand,
        "safety_stock": safety_stock,
        "current_stock": current_stock,
        "formula": formula_str,
    }

    recommendation, _ = RestockRecommendation.objects.update_or_create(
        product=product,
        defaults={
            "recommended_qty": recommended_qty,
            "avg_daily_demand": avg_daily_demand,
            "status": urgency_status,
            "detail": detail,
        },
    )
    return recommendation


def sync_and_get_restock_recommendations(
    status_filter: Optional[str] = None,
    product_id: Optional[int] = None,
):
    """
    Memperbarui rekomendasi untuk produk aktif dan mengembalikan QuerySet
    yang diurutkan berdasarkan prioritas urgensi: critical -> warning -> ok.
    """
    active_products = Product.objects.filter(is_active=True).select_related("category")
    if product_id:
        active_products = active_products.filter(pk=product_id)

    # Sinkronisasi rekomendasi untuk produk aktif
    forecasts = (
        Forecast.objects.filter(horizon_days=7)
        .order_by("product_id", "-generated_at")
    )
    forecast_map = {}
    for f in forecasts:
        if f.product_id not in forecast_map:
            forecast_map[f.product_id] = f

    for p in active_products:
        f = forecast_map.get(p.id)
        avg_demand = None
        if f and f.horizon_days > 0:
            avg_demand = Decimal(str(round(f.total_predicted / f.horizon_days, 2)))
        calculate_restock_recommendation_for_product(p, avg_daily_demand=avg_demand)

    urgency_order = Case(
        When(status="critical", then=Value(1)),
        When(status="warning", then=Value(2)),
        When(status="ok", then=Value(3)),
        default=Value(4),
        output_field=IntegerField(),
    )

    qs = (
        RestockRecommendation.objects.filter(product__is_active=True)
        .select_related("product", "product__category")
        .annotate(urgency_priority=urgency_order)
        .order_by("urgency_priority", "-recommended_qty", "product__name")
    )

    if status_filter:
        qs = qs.filter(status=status_filter.lower())
    if product_id:
        qs = qs.filter(product_id=product_id)

    return qs
