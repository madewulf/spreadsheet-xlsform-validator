"""
URL configuration for the XLSForm validator API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import RedirectView

from .views import SpreadsheetValidationViewSet

router = DefaultRouter()
router.register(r"validate", SpreadsheetValidationViewSet, basename="validate")

urlpatterns = [
    path(
        "", RedirectView.as_view(url="validate/form/", permanent=False), name="api-root"
    ),
    path("", include(router.urls)),
]
