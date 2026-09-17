from django.urls import path

from .views import StockMovementListCreateView

urlpatterns = [
    path("", StockMovementListCreateView.as_view(), name="stock-movement-list-create"),
]
