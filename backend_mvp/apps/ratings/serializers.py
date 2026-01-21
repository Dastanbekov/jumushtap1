"""
Rating API Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import RatingHistory, RatingProtectionLog

User = get_user_model()


class RatingHistorySerializer(serializers.ModelSerializer):
    """Сериализатор истории изменений рейтинга"""
    
    class Meta:
        model = RatingHistory
        fields = [
            'id', 'old_rating', 'new_rating', 'old_count', 'new_count',
            'reason', 'details', 'created_at'
        ]
        read_only_fields = fields


class UserRatingSerializer(serializers.Serializer):
    """Сериализатор детальной информации о рейтинге пользователя"""
    
    rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    distribution = serializers.DictField(child=serializers.IntegerField())
    rating_updated_at = serializers.DateTimeField(allow_null=True)
    is_verified = serializers.BooleanField()


class RatingAnalyticsSerializer(serializers.Serializer):
    """Сериализатор аналитики рейтинговой системы"""
    
    period_days = serializers.IntegerField()
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    blocked_attempts = serializers.IntegerField()
    suspicious_attempts = serializers.IntegerField()
    top_users = serializers.ListField()
    fraud_distribution = serializers.ListField()


class FraudLogSerializer(serializers.ModelSerializer):
    """Сериализатор логов подозрительной активности"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    target_username = serializers.CharField(source='target_user.username', read_only=True, allow_null=True)
    
    class Meta:
        model = RatingProtectionLog
        fields = [
            'id', 'user', 'user_username', 'target_user', 'target_username',
            'action_type', 'details', 'ip_address', 'blocked', 'created_at'
        ]
        read_only_fields = fields
