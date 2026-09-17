from rest_framework import serializers

from apps.products.models import Product

from .models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_name",
            "user",
            "type",
            "qty",
            "movement_date",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, attrs):
        movement_type = attrs.get("type")
        qty = attrs.get("qty")
        product = attrs.get("product")

        if movement_type == StockMovement.Type.IN:
            if qty is not None and qty <= 0:
                raise serializers.ValidationError(
                    {"qty": ["Jumlah stok masuk harus lebih dari 0."]}
                )
        elif movement_type == StockMovement.Type.ADJUST:
            if qty is not None and qty == 0:
                raise serializers.ValidationError(
                    {"qty": ["Jumlah penyesuaian tidak boleh 0."]}
                )
            if product is not None and qty is not None:
                if product.current_stock + qty < 0:
                    raise serializers.ValidationError(
                        {"qty": ["Penyesuaian stok menyebabkan stok menjadi negatif."]}
                    )

        return attrs


class StockSummarySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    stock_status = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "unit",
            "min_stock",
            "current_stock",
            "stock_status",
            "is_active",
        ]
        read_only_fields = fields
