from rest_framework import serializers

from .models import Forecast, RestockRecommendation


class ForecastModelSerializer(serializers.ModelSerializer):
    """Serializer untuk model Forecast."""

    class Meta:
        model = Forecast
        fields = [
            "id",
            "product",
            "horizon_days",
            "generated_at",
            "total_predicted",
            "daily_breakdown",
            "model_name",
            "metrics",
        ]


class RestockRecommendationSerializer(serializers.ModelSerializer):
    """Serializer untuk model RestockRecommendation dengan data produk terkait."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    category_name = serializers.CharField(
        source="product.category.name", read_only=True, default=""
    )
    current_stock = serializers.IntegerField(
        source="product.current_stock", read_only=True
    )
    min_stock = serializers.IntegerField(source="product.min_stock", read_only=True)
    safety_stock = serializers.IntegerField(
        source="product.safety_stock", read_only=True
    )
    lead_time_days = serializers.IntegerField(
        source="product.lead_time_days", read_only=True
    )
    avg_daily_demand = serializers.FloatField(read_only=True)

    class Meta:
        model = RestockRecommendation
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "category_name",
            "current_stock",
            "min_stock",
            "safety_stock",
            "lead_time_days",
            "recommended_qty",
            "avg_daily_demand",
            "status",
            "detail",
            "generated_at",
        ]
