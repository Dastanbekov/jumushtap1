"""
Rating API URL Configuration
"""

from django.urls import path
from .views import (
    UserRatingView,
    RatingHistoryView,
    RatingAnalyticsView,
    FraudLogsView,
    RecalculateRatingView
)

urlpatterns = [
    # Рейтинг пользователя
    path('ratings/<int:user_id>/', UserRatingView.as_view(), name='user-rating'),
    path('ratings/<int:user_id>/history/', RatingHistoryView.as_view(), name='rating-history'),
    path('ratings/<int:user_id>/recalculate/', RecalculateRatingView.as_view(), name='recalculate-rating'),
    
    # Админские эндпоинты
    path('ratings/analytics/', RatingAnalyticsView.as_view(), name='rating-analytics'),
    path('ratings/fraud-logs/', FraudLogsView.as_view(), name='fraud-logs'),
]
