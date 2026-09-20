from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.products.models import Product
from shared.envelope import APIResponse
from shared.exceptions import NotFoundError

from .services import get_or_generate_product_forecast


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
