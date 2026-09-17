import datetime
from decimal import Decimal
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.products.models import Product
from apps.sales.models import Sale, SaleItem
from shared.envelope import APIResponse


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_products = Product.objects.filter(is_active=True)
        total_products = active_products.count()
        low_stock_count = active_products.filter(
            current_stock__gt=0, current_stock__lte=models.F("min_stock")
        ).count()
        critical_stock_count = active_products.filter(current_stock__lte=0).count()

        # Hitung total estimasi nilai aset modal stok produk aktif
        stock_value_result = active_products.filter(current_stock__gt=0).aggregate(
            val=Sum(
                F("current_stock") * F("purchase_price"),
                output_field=models.DecimalField(max_digits=14, decimal_places=2),
            )
        )
        total_stock_value = stock_value_result["val"] or Decimal("0.00")

        # Penjualan hari ini
        today = timezone.localdate()
        today_sales_total = (
            Sale.objects.filter(sale_date=today).aggregate(tot=Sum("total"))["tot"]
            or Decimal("0.00")
        )
        today_sales_count = Sale.objects.filter(sale_date=today).count()
        today_items_sold = (
            SaleItem.objects.filter(sale__sale_date=today).aggregate(qty=Sum("qty"))[
                "qty"
            ]
            or 0
        )

        data = {
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "critical_stock_count": critical_stock_count,
            "total_stock_value": str(total_stock_value),
            "today_sales_total": str(today_sales_total),
            "today_sales_count": today_sales_count,
            "today_items_sold": today_items_sold,
        }

        return APIResponse(
            data=data,
            status_code=status.HTTP_200_OK,
            message="Ringkasan dashboard berhasil diambil",
        )


class DashboardTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_trend_points(self, days: int, today: datetime.date) -> list[dict]:
        start_date = today - datetime.timedelta(days=days - 1)

        sales_by_date = {
            r["sale_date"]: r["total"]
            for r in (
                Sale.objects.filter(sale_date__gte=start_date, sale_date__lte=today)
                .values("sale_date")
                .annotate(total=Sum("total"))
                .order_by("sale_date")
            )
        }

        items_by_date = {
            r["date"]: r["qty"]
            for r in (
                SaleItem.objects.filter(
                    sale__sale_date__gte=start_date, sale__sale_date__lte=today
                )
                .values(date=F("sale__sale_date"))
                .annotate(qty=Sum("qty"))
                .order_by("date")
            )
        }

        points = []
        curr = start_date
        while curr <= today:
            tot = sales_by_date.get(curr, Decimal("0.00"))
            qty = items_by_date.get(curr, 0)
            points.append(
                {
                    "date": curr.isoformat(),
                    "total": str(tot),
                    "qty": qty,
                }
            )
            curr += datetime.timedelta(days=1)

        return points

    def get(self, request):
        today = timezone.localdate()
        weekly = self._get_trend_points(7, today)
        monthly = self._get_trend_points(30, today)

        period = request.query_params.get("period", "").lower()

        data = {
            "weekly": weekly,
            "monthly": monthly,
        }

        if period in ("weekly", "7d", "7"):
            data["period"] = "weekly"
            data["points"] = weekly
        elif period in ("monthly", "30d", "30"):
            data["period"] = "monthly"
            data["points"] = monthly

        return APIResponse(
            data=data,
            status_code=status.HTTP_200_OK,
            message="Tren penjualan berhasil diambil",
        )
