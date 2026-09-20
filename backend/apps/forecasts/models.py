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
