from rest_framework.permissions import BasePermission

from .models import User


class IsOwner(BasePermission):
    message = "Hanya Owner yang dapat melakukan aksi ini."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.OWNER
        )
