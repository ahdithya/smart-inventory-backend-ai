from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    unit = models.CharField(max_length=20)
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    min_stock = models.PositiveIntegerField(default=10)
    safety_stock = models.PositiveIntegerField(default=5)
    lead_time_days = models.PositiveIntegerField(
        default=7, validators=[MinValueValidator(1)]
    )
    expiry_days = models.PositiveIntegerField(null=True, blank=True)
    current_stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["category"]),
            models.Index(fields=["current_stock"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return "Kritis"
        elif self.current_stock <= self.min_stock:
            return "Menipis"
        return "Aman"

    def save(self, *args, **kwargs):
        if not self.sku:
            last_id = (
                Product.objects.order_by("-id").values_list("id", flat=True).first()
                or 0
            )
            next_id = last_id + 1
            candidate = f"PROD-{next_id:04d}"
            while Product.objects.filter(sku=candidate).exists():
                next_id += 1
                candidate = f"PROD-{next_id:04d}"
            self.sku = candidate
        super().save(*args, **kwargs)
