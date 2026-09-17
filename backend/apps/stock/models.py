from django.db import models
from django.utils import timezone


class StockMovement(models.Model):
    class Type(models.TextChoices):
        IN = "IN", "In"
        ADJUST = "ADJUST", "Adjust"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    type = models.CharField(max_length=6, choices=Type.choices)
    qty = models.IntegerField()
    movement_date = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-movement_date", "-created_at"]
        indexes = [
            models.Index(fields=["product", "movement_date"]),
            models.Index(fields=["type"]),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.type} {self.qty})"
