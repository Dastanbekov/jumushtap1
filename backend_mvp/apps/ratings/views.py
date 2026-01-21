"""
Rating API Views

Provides endpoints for rating retrieval, history, and analytics.
"""

from rest_framework import generics, views, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import RatingHistory, RatingProtectionLog
from .services import RatingService
from .serializers import (
    RatingHistorySerializer,
    UserRatingSerializer,
    RatingAnalyticsSerializer,
    FraudLogSerializer
)

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """Разрешение только для админов"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or 
            getattr(request.user, 'role', '') == 'admin'
        )


class UserRatingView(views.APIView):
    """
    GET /api/v1/ratings/{user_id}/
    
    Получить детальную информацию о рейтинге пользователя.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        rating_details = RatingService.get_user_rating_details(user)
        
        serializer = UserRatingSerializer(rating_details)
        return Response(serializer.data)


class RatingHistoryView(generics.ListAPIView):
    """
    GET /api/v1/ratings/{user_id}/history/
    
    Получить историю изменений рейтинга пользователя.
    Пользователь может видеть только свою историю.
    Админы могут видеть историю любого пользователя.
    """
    serializer_class = RatingHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, pk=user_id)
        
        # Проверка прав: только своя история или админ
        if self.request.user.id != user.id and not self.request.user.is_staff:
            if getattr(self.request.user, 'role', '') != 'admin':
                return RatingHistory.objects.none()
        
        return RatingHistory.objects.filter(user=user).order_by('-created_at')[:50]


class RatingAnalyticsView(views.APIView):
    """
    GET /api/v1/ratings/analytics/
    
    Получить аналитику по системе рейтинга.
    Только для администраторов.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        days = min(days, 365)  # Максимум год
        
        analytics = RatingService.get_analytics(days=days)
        serializer = RatingAnalyticsSerializer(analytics)
        
        return Response(serializer.data)


class FraudLogsView(generics.ListAPIView):
    """
    GET /api/v1/ratings/fraud-logs/
    
    Получить логи подозрительной активности.
    Только для администраторов.
    """
    serializer_class = FraudLogSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = RatingProtectionLog.objects.all().order_by('-created_at')
        
        # Фильтры
        blocked_only = self.request.query_params.get('blocked_only', 'false')
        if blocked_only.lower() == 'true':
            queryset = queryset.filter(blocked=True)
        
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        return queryset[:100]


class RecalculateRatingView(views.APIView):
    """
    POST /api/v1/ratings/{user_id}/recalculate/
    
    Принудительный пересчёт рейтинга пользователя.
    Только для администраторов.
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        
        old_rating = user.rating
        new_rating = RatingService.recalculate_rating(
            user=user,
            reason='admin_adjustment',
            triggered_by=request.user
        )
        
        return Response({
            'user_id': user.id,
            'old_rating': float(old_rating),
            'new_rating': float(new_rating),
            'message': 'Rating recalculated successfully'
        })
