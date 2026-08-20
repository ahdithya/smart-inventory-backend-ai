from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "unit",
            "purchase_price",
            "selling_price",
            "min_stock",
            "safety_stock",
            "lead_time_days",
            "expiry_days",
            "current_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "current_stock", "created_at", "updated_at"]
