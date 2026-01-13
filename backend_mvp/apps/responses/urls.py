from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResponseViewSet

router = DefaultRouter()
router.register(r'responses', ResponseViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
