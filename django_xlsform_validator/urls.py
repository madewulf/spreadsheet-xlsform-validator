"""
URL configuration for the XLSForm validator API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SpreadsheetValidationViewSet

app_name = 'django_xlsform_validator'

router = DefaultRouter()
router.register(r"validate", SpreadsheetValidationViewSet, basename="validate")

urlpatterns = [
    path("", include(router.urls)),
]
