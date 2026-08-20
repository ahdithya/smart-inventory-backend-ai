from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from shared.envelope import APIResponse

from .models import Product
from .serializers import ProductSerializer


class ProductList(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return APIResponse(
            data={"products": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Produk berhasil diambil",
        )

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
            message="Produk berhasil dibuat",
        )


class ProductDetail(APIView):
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise NotFound("Produk tidak ditemukan.")

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
        product.delete()
        return APIResponse(status_code=status.HTTP_204_NO_CONTENT)
