from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import BusinessProfile, User


@receiver(post_save, sender=User)
def create_business_profile(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.role != User.Role.OWNER:
        return

    business_name = getattr(instance, "_business_name", None) or instance.username
    business_type = (
        getattr(instance, "_business_type", None) or BusinessProfile.BusinessType.OTHERS
    )

    BusinessProfile.objects.create(
        owner=instance, business_name=business_name, business_type=business_type
    )
