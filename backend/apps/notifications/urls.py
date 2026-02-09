"""
URL Configuration for Notifications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DeviceViewSet, NotificationViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
