from collections import defaultdict
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.products.models import Product
from shared.envelope import APIResponse
from shared.exceptions import NotFoundError

from .models import Sale, SaleItem
from .serializers import (
    SaleCreateSerializer,
    SaleDetailSerializer,
    SaleListSerializer,
)


class SaleListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sales = Sale.objects.all().select_related("user").prefetch_related("items")

        start_date = request.query_params.get("start_date")
        if start_date:
            sales = sales.filter(sale_date__gte=start_date)

        end_date = request.query_params.get("end_date")
        if end_date:
            sales = sales.filter(sale_date__lte=end_date)

        user_id = request.query_params.get("user")
        if user_id:
            sales = sales.filter(user_id=user_id)

        serializer = SaleListSerializer(sales, many=True)
        return APIResponse(
            data={"sales": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Daftar penjualan berhasil diambil",
        )

    def post(self, request):
        serializer = SaleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data["items"]
        sale_date = serializer.validated_data.get("sale_date") or timezone.localdate()

        product_ids = [item["product"].pk for item in items_data]

        with transaction.atomic():
            # Kunci baris database untuk mencegah race condition pemotongan stok
            products = Product.objects.select_for_update().filter(pk__in=product_ids)
            product_map = {p.pk: p for p in products}

            qty_by_pk = defaultdict(int)
            for item in items_data:
                qty_by_pk[item["product"].pk] += item["qty"]

            # Validasi ulang stok di dalam transaksi terkunci
            for pk, total_qty in qty_by_pk.items():
                prod = product_map.get(pk)
                if not prod or not prod.is_active:
                    name = prod.name if prod else f"ID {pk}"
                    raise ValidationError(
                        {"items": [f"Produk '{name}' tidak aktif atau tidak ditemukan."]}
                    )
                if total_qty > prod.current_stock:
                    raise ValidationError(
                        {
                            "items": [
                                f"Stok untuk '{prod.name}' tidak mencukupi (tersedia: {prod.current_stock}, diminta: {total_qty})."
                            ]
                        }
                    )

            # Buat header transaksi penjualan
            sale = Sale.objects.create(
                user=request.user,
                sale_date=sale_date,
                total=Decimal("0.00"),
            )

            total_amount = Decimal("0.00")
            sale_items = []
            for item in items_data:
                prod = product_map[item["product"].pk]
                unit_price = (
                    item["unit_price"]
                    if item.get("unit_price") is not None
                    else prod.selling_price
                )
                qty = item["qty"]
                subtotal = unit_price * qty
                total_amount += subtotal

                sale_items.append(
                    SaleItem(
                        sale=sale,
                        product=prod,
                        qty=qty,
                        unit_price=unit_price,
                    )
                )

            SaleItem.objects.bulk_create(sale_items)
            sale.total = total_amount
            sale.save(update_fields=["total"])

            # Potong stok produk secara atomik
            for pk, total_qty in qty_by_pk.items():
                prod = product_map[pk]
                prod.current_stock -= total_qty
                prod.save(update_fields=["current_stock"])

        # Reload detail transaksi untuk respons lengkap
        sale = (
            Sale.objects.select_related("user")
            .prefetch_related("items__product")
            .get(pk=sale.pk)
        )
        return APIResponse(
            data=SaleDetailSerializer(sale).data,
            status_code=status.HTTP_201_CREATED,
            message="Transaksi penjualan berhasil dicatat",
        )


class SaleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        sale = (
            Sale.objects.select_related("user")
            .prefetch_related("items__product")
            .filter(pk=pk)
            .first()
        )
        if not sale:
            raise NotFoundError("Transaksi penjualan tidak ditemukan.")

        serializer = SaleDetailSerializer(sale)
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Detail penjualan berhasil diambil",
        )
