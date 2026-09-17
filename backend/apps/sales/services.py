import datetime
from typing import Any, Union
from django.db.models import F, Sum
from django.utils import timezone

from apps.products.models import Product

from .models import SaleItem


def get_daily_sales_history(
    product_id: Union[int, Product],
    days: int = 90,
    end_date: Union[datetime.date, None] = None,
) -> list[dict[str, Any]]:
    """
    Mengumpulkan riwayat penjualan harian suatu produk untuk input modul forecasting.
    
    Args:
        product_id: ID produk (int) atau instance Product.
        days: Jumlah hari ke belakang (default: 90 hari).
        end_date: Tanggal akhir jendela waktu (default: hari ini).
        
    Returns:
        List dictionary berisi [{"date": "YYYY-MM-DD", "qty": N}, ...] terurut kronologis (ascending).
        Jika produk tidak memiliki riwayat penjualan, mengembalikan list kosong [].
    """
    if hasattr(product_id, "pk"):
        target_product_id = product_id.pk
    else:
        target_product_id = int(product_id)
        if not Product.objects.filter(pk=target_product_id).exists():
            raise Product.DoesNotExist(f"Produk dengan ID {target_product_id} tidak ditemukan.")

    if end_date is None:
        end_date = timezone.localdate()

    start_date = end_date - datetime.timedelta(days=days - 1)

    records = (
        SaleItem.objects.filter(
            product_id=target_product_id,
            sale__sale_date__gte=start_date,
            sale__sale_date__lte=end_date,
        )
        .values(date=F("sale__sale_date"))
        .annotate(qty=Sum("qty"))
        .order_by("date")
    )

    return [
        {
            "date": r["date"].isoformat() if hasattr(r["date"], "isoformat") else str(r["date"]),
            "qty": r["qty"],
        }
        for r in records
    ]
