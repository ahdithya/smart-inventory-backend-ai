from rest_framework import serializers

from .models import Forecast


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
