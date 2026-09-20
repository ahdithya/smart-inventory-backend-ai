from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.products.models import Product
from shared.envelope import APIResponse
from shared.exceptions import NotFoundError

from .serializers import RestockRecommendationSerializer
from .services import (
    get_or_generate_product_forecast,
    sync_and_get_restock_recommendations,
)


class ForecastListView(APIView):
    """
    Endpoint GET /api/forecasts/
    Menyajikan data peramalan untuk seluruh produk aktif atau produk spesifik (?product_id=X).
    Menggunakan cache 6 jam (BR-12) dan fallback stale=True (BR-15).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get("product_id")
        force_refresh_str = request.query_params.get("force_refresh", "")
        force_refresh = force_refresh_str.lower() in ("true", "1")

        if product_id:
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                raise NotFoundError(f"Produk dengan ID {product_id} tidak ditemukan.")

            forecast_data = get_or_generate_product_forecast(
                product, force_refresh=force_refresh
            )
            return APIResponse(
                data=forecast_data,
                status_code=status.HTTP_200_OK,
                message="Data peramalan produk berhasil diambil",
            )

        # Seluruh produk aktif
        products = Product.objects.filter(is_active=True).order_by("name")
        results = []
        for prod in products:
            data = get_or_generate_product_forecast(prod, force_refresh=force_refresh)
            results.append(data)

        return APIResponse(
            data={"forecasts": results},
            status_code=status.HTTP_200_OK,
            message="Daftar peramalan berhasil diambil",
        )


class RestockRecommendationListView(APIView):
    """
    Endpoint GET /api/restock-recommendations/
    Menyajikan daftar rekomendasi restock untuk seluruh produk aktif atau produk spesifik (?product_id=X).
    Hasil diurutkan berdasarkan tingkat urgensi: critical -> warning -> ok (DATABASE §2.8 & SRS 3.7).
    Mendukung filter query parameter ?status=critical|warning|ok dan ?product_id=X.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get("product_id")
        status_filter = request.query_params.get("status")

        if product_id:
            try:
                Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                raise NotFoundError(f"Produk dengan ID {product_id} tidak ditemukan.")

        qs = sync_and_get_restock_recommendations(
            status_filter=status_filter,
            product_id=int(product_id) if product_id else None,
        )
        serializer = RestockRecommendationSerializer(qs, many=True)
        return APIResponse(
            data={"recommendations": serializer.data},
            status_code=status.HTTP_200_OK,
            message="Daftar rekomendasi restock berhasil diambil",
        )
