from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Forecast(models.Model):
    """
    Menyimpan hasil peramalan permintaan produk untuk horizon 7 dan 14 hari.
    Satu produk maksimal memiliki 2 entri aktif (7 dan 14 hari).
    Sesuai docs/DATABASE.md §2.7.
    """

    HORIZON_CHOICES = (
        (7, "7 Hari"),
        (14, "14 Hari"),
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="forecasts",
    )
    horizon_days = models.IntegerField(choices=HORIZON_CHOICES)
    generated_at = models.DateTimeField()
    total_predicted = models.IntegerField(default=0)
    daily_breakdown = models.JSONField(default=list)
    model_name = models.CharField(max_length=50)
    metrics = models.JSONField(default=dict)

    class Meta:
        db_table = "forecasts"
        unique_together = ("product", "horizon_days")
        indexes = [
            models.Index(fields=["product", "horizon_days"]),
            models.Index(fields=["generated_at"]),
        ]
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Forecast {self.product.name} ({self.horizon_days}d) - {self.total_predicted}"


class RestockRecommendation(models.Model):
    """
    Menyimpan rekomendasi kuantitas restock produk berdasarkan hasil peramalan,
    lead time, safety stock, dan stok saat ini.
    Sesuai docs/DATABASE.md §2.8.
    """

    STATUS_CHOICES = (
        ("critical", "Critical"),
        ("warning", "Warning"),
        ("ok", "OK"),
    )

    product = models.OneToOneField(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="restock_recommendation",
    )
    generated_at = models.DateTimeField(auto_now=True)
    recommended_qty = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )
    avg_daily_demand = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    detail = models.JSONField(default=dict)

    class Meta:
        db_table = "restock_recommendations"
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["status"]),
            models.Index(fields=["generated_at"]),
        ]
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Restock {self.product.name}: {self.recommended_qty} ({self.status})"
