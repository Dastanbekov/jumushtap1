"""
URL Configuration for Jobs app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import JobViewSet, JobApplicationViewSet, CheckInViewSet

app_name = 'jobs'

router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', JobApplicationViewSet, basename='application')
router.register(r'checkins', CheckInViewSet, basename='checkin')

urlpatterns = [
    path('', include(router.urls)),
]
