from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    stock_status = serializers.CharField(read_only=True)
    sku = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "category",
            "category_name",
            "created_by",
            "unit",
            "purchase_price",
            "selling_price",
            "min_stock",
            "safety_stock",
            "lead_time_days",
            "expiry_days",
            "current_stock",
            "stock_status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "current_stock",
            "stock_status",
            "created_at",
            "updated_at",
        ]

    def validate_sku(self, value):
        if value:
            qs = Product.objects.filter(sku=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("SKU sudah digunakan.")
        return value
