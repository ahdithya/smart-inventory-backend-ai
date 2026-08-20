from django.urls import path

from .views import ProductDetail, ProductList

urlpatterns = [
    path("", ProductList.as_view(), name="product-list"),
    path("<int:pk>/", ProductDetail.as_view(), name="product-detail"),
]
