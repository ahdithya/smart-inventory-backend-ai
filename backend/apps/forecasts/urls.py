from django.urls import path
from .views import ForecastListView

app_name = "forecasts"

urlpatterns = [
    path("", ForecastListView.as_view(), name="forecast-list"),
]
