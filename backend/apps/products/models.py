from django.db import models


class Product(models.Model):
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=20)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stock = models.PositiveIntegerField(default=10)
    safety_stock = models.PositiveIntegerField(default=5)
    lead_time_days = models.PositiveIntegerField(default=7)
    expiry_days = models.PositiveIntegerField(null=True, blank=True)
    current_stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
