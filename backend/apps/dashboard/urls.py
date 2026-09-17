from django.urls import path

from .views import DashboardSummaryView, DashboardTrendView

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("trend/", DashboardTrendView.as_view(), name="dashboard-trend"),
]
