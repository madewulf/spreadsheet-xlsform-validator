"""
URL configuration for the XLSForm validator API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SpreadsheetValidationViewSet

router = DefaultRouter()
router.register(r'validate', SpreadsheetValidationViewSet, basename='validate')

urlpatterns = [
    path('', include(router.urls)),
]
