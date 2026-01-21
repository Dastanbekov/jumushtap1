"""
Rating System Models

Enterprise-grade models for rating history tracking and fraud protection.
"""

from django.db import models
from django.conf import settings


class RatingHistory(models.Model):
    """
    Аудит всех изменений рейтинга пользователя.
    Позволяет отслеживать историю и откатывать изменения при необходимости.
    """
    REASON_CHOICES = (
        ('review_added', 'Review Added'),
        ('review_updated', 'Review Updated'),
        ('review_deleted', 'Review Deleted'),
        ('fraud_detected', 'Fraud Detected'),
        ('admin_adjustment', 'Admin Adjustment'),
        ('recalculation', 'Periodic Recalculation'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rating_history'
    )
    old_rating = models.DecimalField(max_digits=3, decimal_places=2)
    new_rating = models.DecimalField(max_digits=3, decimal_places=2)
    old_count = models.PositiveIntegerField(default=0)
    new_count = models.PositiveIntegerField(default=0)
    review = models.ForeignKey(
        'reviews.Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rating_changes'
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rating_changes_made'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rating History'
        verbose_name_plural = 'Rating Histories'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['reason']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.old_rating} -> {self.new_rating} ({self.reason})"


class RatingProtectionLog(models.Model):
    """
    Логирование попыток накрутки и подозрительной активности.
    Используется для анализа и блокировки злоумышленников.
    """
    ACTION_CHOICES = (
        ('rate_limit', 'Rate Limit Exceeded'),
        ('pattern_detected', 'Suspicious Pattern Detected'),
        ('ip_duplicate', 'Duplicate IP Address'),
        ('circular_rating', 'Circular Rating Attempt'),
        ('new_account_spam', 'New Account Spam'),
        ('suspicious_timing', 'Suspicious Timing Pattern'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fraud_logs'
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fraud_target_logs',
        null=True,
        blank=True
    )
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Fraud Protection Log'
        verbose_name_plural = 'Fraud Protection Logs'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['blocked']),
        ]

    def __str__(self):
        status = "BLOCKED" if self.blocked else "LOGGED"
        return f"[{status}] {self.user.username} - {self.action_type}"


class RatingConfig(models.Model):
    """
    Конфигурация системы рейтинга.
    Singleton модель для хранения настроек.
    """
    # Веса для расчёта
    recency_weight = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.3,
        help_text="Weight for recent reviews (0-1)"
    )
    verified_user_weight = models.DecimalField(
        max_digits=3, decimal_places=2, default=1.5,
        help_text="Multiplier for verified user reviews"
    )
    
    # Защита от накрутки
    min_review_interval_minutes = models.PositiveIntegerField(
        default=60,
        help_text="Minimum minutes between reviews from same user"
    )
    max_reviews_per_day = models.PositiveIntegerField(
        default=10,
        help_text="Maximum reviews a user can give per day"
    )
    new_account_days = models.PositiveIntegerField(
        default=7,
        help_text="Days after which account is no longer 'new'"
    )
    
    # Пороги подозрительности
    circular_rating_check_depth = models.PositiveIntegerField(
        default=3,
        help_text="Depth for detecting circular rating patterns"
    )
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rating Configuration'
        verbose_name_plural = 'Rating Configuration'

    def save(self, *args, **kwargs):
        # Singleton: всегда обновляем запись с id=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        """Получить текущую конфигурацию (создаёт дефолтную если нет)"""
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def __str__(self):
        return "Rating System Configuration"
