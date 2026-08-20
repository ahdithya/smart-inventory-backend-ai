from django.urls import path

from .views import CategoryDetail, CategoryList

urlpatterns = [
    path("", CategoryList.as_view(), name="category-list"),
    path("<int:pk>/", CategoryDetail.as_view(), name="category-detail"),
]
