from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import IsOwner
from shared.envelope import APIResponse
from shared.exceptions import NotFoundError

from .models import Product
from .serializers import ProductSerializer


class ProductList(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwner()]
        return [IsAuthenticated()]

    def get(self, request):
        products = Product.objects.all().select_related("category")

        category_id = request.query_params.get("category")
        if category_id:
            products = products.filter(category_id=category_id)

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ("true", "1"):
                products = products.filter(is_active=True)
            elif is_active.lower() in ("false", "0"):
                products = products.filter(is_active=False)

        serializer = ProductSerializer(products, many=True)
        return APIResponse(
            data={"products": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Produk berhasil diambil",
        )

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
            message="Produk berhasil dibuat",
        )


class ProductDetail(APIView):
    def get_permissions(self):
        if self.request.method in ("PUT", "DELETE"):
            return [IsOwner()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Product.objects.select_related("category").get(pk=pk)
        except Product.DoesNotExist:
            raise NotFoundError("Produk tidak ditemukan.")

    def get(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductSerializer(product)
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Produk berhasil diambil",
        )

    def put(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Produk berhasil diperbarui",
        )

    def delete(self, request, pk):
        product = self.get_object(pk)
        product.is_active = False
        product.save(update_fields=["is_active"])
        return APIResponse(status_code=status.HTTP_204_NO_CONTENT)
