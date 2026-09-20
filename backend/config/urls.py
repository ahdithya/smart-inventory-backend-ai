"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from apps.accounts.views import BusinessProfileView, UserListView, UserRoleUpdateView
from apps.forecasts.views import RestockRecommendationListView
from apps.stock.views import StockListView
from django.contrib import admin
from django.urls import include, path, re_path

api_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("categories/", include("apps.categories.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("products/", include("apps.products.urls")),
    path("sales/", include("apps.sales.urls")),
    path("stock-movements/", include("apps.stock.urls")),
    path("stock/", StockListView.as_view(), name="stock-list"),
    path("users/", UserListView.as_view(), name="user-list"),
    path(
        "users/<int:pk>/role/",
        UserRoleUpdateView.as_view(),
        name="user-role-update",
    ),
    path(
        "business-profile/", BusinessProfileView.as_view(), name="business-profile"
    ),
    path("forecasts/", include("apps.forecasts.urls")),
    path(
        "restock-recommendations/",
        RestockRecommendationListView.as_view(),
        name="restock-recommendations",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^api/(?:v1/)?", include(api_patterns)),
]
