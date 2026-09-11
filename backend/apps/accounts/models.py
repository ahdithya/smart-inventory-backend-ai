from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        STAFF = "staff", "Staff"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class BusinessProfile(models.Model):
    class BusinessType(models.TextChoices):
        FOOD = "food", "Food"
        BEVERAGE = "beverage", "Beverage"
        FASHION = "fashion", "Fashion"
        RETAIL = "retail", "Retail"
        SERVICE = "service", "Service"
        OTHERS = "others", "Others"

    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="business_profile"
    )
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(
        max_length=20, choices=BusinessType.choices, default=BusinessType.OTHERS
    )
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name
