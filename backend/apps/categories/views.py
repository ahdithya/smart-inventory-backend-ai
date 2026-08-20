from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.shared.envelope import APIResponse

from .models import Category
from .serializers import CategorySerializer


class CategoryList(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return APIResponse(
            data={"categories": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Kategori berhasil diambil",
        )

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_201_CREATED,
            message="Kategori berhasil dibuat",
        )


class CategoryDetail(APIView):
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            raise NotFound("Kategori tidak ditemukan.")

    def get(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category)
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Kategori berhasil diambil",
        )

    def put(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return APIResponse(
            data=serializer.data,
            status_code=status.HTTP_200_OK,
            message="Kategori berhasil diperbarui",
        )

    def delete(self, request, pk):
        category = self.get_object(pk)
        category.delete()
        return APIResponse(status_code=status.HTTP_204_NO_CONTENT)
