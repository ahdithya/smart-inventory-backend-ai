from collections import defaultdict
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers

from apps.products.models import Product

from .models import Sale, SaleItem


class SaleItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=True
    )
    qty = serializers.IntegerField(min_value=1, required=True)
    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        default=None,
    )

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            if "product_id" in data and "product" not in data:
                data["product"] = data["product_id"]
            if "quantity" in data and "qty" not in data:
                data["qty"] = data["quantity"]
        return super().to_internal_value(data)


class SaleItemDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = SaleItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "qty",
            "unit_price",
            "subtotal",
        ]

    def get_subtotal(self, obj):
        return obj.qty * obj.unit_price


class SaleCreateSerializer(serializers.Serializer):
    sale_date = serializers.DateField(default=timezone.localdate, required=False)
    items = SaleItemInputSerializer(many=True, required=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Transaksi harus memiliki minimal 1 item.")
        return value

    def validate(self, attrs):
        items_data = attrs.get("items", [])
        if not items_data:
            raise serializers.ValidationError(
                {"items": ["Transaksi harus memiliki minimal 1 item."]}
            )

        # Kelompokkan kuantitas per produk jika ada duplikat dalam satu transaksi
        qty_by_product = defaultdict(int)
        for item in items_data:
            product = item["product"]
            if not product.is_active:
                raise serializers.ValidationError(
                    {"items": [f"Produk '{product.name}' tidak aktif dan tidak dapat dijual."]}
                )
            qty_by_product[product] += item["qty"]

        # Validasi stok mencukupi
        for product, total_qty in qty_by_product.items():
            if total_qty > product.current_stock:
                raise serializers.ValidationError(
                    {
                        "items": [
                            f"Stok untuk '{product.name}' tidak mencukupi (tersedia: {product.current_stock}, diminta: {total_qty})."
                        ]
                    }
                )

        return attrs


class SaleListSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            "id",
            "sale_date",
            "total",
            "user",
            "user_username",
            "items_count",
            "created_at",
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    items = SaleItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id",
            "sale_date",
            "total",
            "user",
            "user_username",
            "items",
            "created_at",
        ]
