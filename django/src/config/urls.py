from django.contrib import admin
from django.urls import path

from config.rest.health_check_view import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view()),
]
