from django.db import models, transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.products.models import Product
from shared.envelope import APIResponse

from .models import StockMovement
from .serializers import StockMovementSerializer, StockSummarySerializer


class StockMovementListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        movements = StockMovement.objects.all().select_related("product", "user")

        product_id = request.query_params.get("product")
        if product_id:
            movements = movements.filter(product_id=product_id)

        movement_type = request.query_params.get("type")
        if movement_type:
            movements = movements.filter(type=movement_type.upper())

        serializer = StockMovementSerializer(movements, many=True)
        return APIResponse(
            data={"stock_movements": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Riwayat pergerakan stok berhasil diambil",
        )

    def post(self, request):
        movement_type = request.data.get("type")
        if (
            movement_type == StockMovement.Type.ADJUST
            and request.user.role != User.Role.OWNER
        ):
            raise PermissionDenied("Hanya Owner yang dapat melakukan penyesuaian stok.")

        serializer = StockMovementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            product = Product.objects.select_for_update().get(
                pk=serializer.validated_data["product"].pk
            )
            qty = serializer.validated_data["qty"]

            if serializer.validated_data[
                "type"
            ] == StockMovement.Type.ADJUST and (product.current_stock + qty < 0):
                raise ValidationError(
                    {"qty": ["Penyesuaian stok menyebabkan stok menjadi negatif."]}
                )

            product.current_stock += qty
            product.save(update_fields=["current_stock"])

            movement = serializer.save(user=request.user)

        return APIResponse(
            data=StockMovementSerializer(movement).data,
            status_code=status.HTTP_201_CREATED,
            message="Pergerakan stok berhasil dicatat",
        )


class StockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.all().select_related("category")

        category_id = request.query_params.get("category")
        if category_id:
            products = products.filter(category_id=category_id)

        status_filter = request.query_params.get("status")
        if status_filter:
            status_lower = status_filter.lower()
            if status_lower == "kritis":
                products = products.filter(current_stock__lte=0)
            elif status_lower == "menipis":
                products = products.filter(
                    current_stock__gt=0, current_stock__lte=models.F("min_stock")
                )
            elif status_lower == "aman":
                products = products.filter(current_stock__gt=models.F("min_stock"))

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            products = products.filter(is_active=is_active.lower() in ("true", "1"))

        serializer = StockSummarySerializer(products, many=True)
        return APIResponse(
            data={"stock": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Daftar stok berhasil diambil",
        )
