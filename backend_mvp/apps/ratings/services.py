"""
Rating Service Layer

Enterprise-grade business logic for rating calculation and fraud protection.
Implements weighted ratings, anti-fraud checks, and audit logging.
"""

from decimal import Decimal
from datetime import timedelta
from typing import Optional, Tuple

from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from django.conf import settings

from apps.users.models import User
from apps.reviews.models import Review
from .models import RatingHistory, RatingProtectionLog, RatingConfig


class FraudProtectionService:
    """
    Сервис защиты от накрутки рейтинга.
    Реализует многоуровневую проверку подозрительной активности.
    """
    
    @staticmethod
    def get_client_ip(request) -> Optional[str]:
        """Извлечь IP адрес клиента из запроса"""
        if request is None:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def get_user_agent(request) -> str:
        """Извлечь User-Agent из запроса"""
        if request is None:
            return ''
        return request.META.get('HTTP_USER_AGENT', '')
    
    @classmethod
    def check_rate_limit(cls, from_user: User, config: RatingConfig) -> Tuple[bool, str]:
        """
        Проверка rate limit на создание отзывов.
        Returns: (is_violation, reason)
        """
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Проверка дневного лимита
        daily_count = Review.objects.filter(
            from_user=from_user,
            created_at__gte=today_start
        ).count()
        
        if daily_count >= config.max_reviews_per_day:
            return True, f"Превышен дневной лимит отзывов ({config.max_reviews_per_day})"
        
        # Проверка минимального интервала
        min_interval = now - timedelta(minutes=config.min_review_interval_minutes)
        recent_review = Review.objects.filter(
            from_user=from_user,
            created_at__gte=min_interval
        ).first()
        
        if recent_review:
            return True, f"Минимальный интервал между отзывами: {config.min_review_interval_minutes} минут"
        
        return False, ""
    
    @classmethod
    def check_ip_duplicate(cls, from_user: User, to_user: User, ip_address: Optional[str]) -> Tuple[bool, str]:
        """
        Проверка на совпадение IP адресов.
        Подозрительно, если reviewer и reviewee с одного IP.
        """
        if not ip_address:
            return False, ""
        
        # Проверяем, был ли to_user когда-либо с этого IP
        same_ip_reviews = Review.objects.filter(
            from_user=to_user,
            ip_address=ip_address
        ).exists()
        
        if same_ip_reviews:
            return True, f"Подозрительное совпадение IP адресов"
        
        return False, ""
    
    @classmethod
    def check_circular_rating(cls, from_user: User, to_user: User, config: RatingConfig) -> Tuple[bool, str]:
        """
        Проверка на круговую накрутку (A оценивает B, B оценивает A).
        """
        # Прямая проверка: to_user уже оценивал from_user?
        reverse_review = Review.objects.filter(
            from_user=to_user,
            to_user=from_user
        ).exists()
        
        if reverse_review:
            # Это может быть легитимно (оба участника сделки оценивают друг друга)
            # Но помечаем для дополнительного анализа
            recent_timeframe = timezone.now() - timedelta(days=7)
            recent_reverse = Review.objects.filter(
                from_user=to_user,
                to_user=from_user,
                created_at__gte=recent_timeframe
            ).exists()
            
            if recent_reverse:
                return False, ""  # Нормально для недавних сделок
            
        return False, ""
    
    @classmethod
    def check_new_account_spam(cls, from_user: User, rating: int, config: RatingConfig) -> Tuple[bool, str]:
        """
        Проверка на спам от новых аккаунтов (только 5 звёзд).
        """
        account_age = timezone.now() - from_user.date_joined
        is_new_account = account_age.days < config.new_account_days
        
        if is_new_account and rating == 5:
            # Проверяем, все ли отзывы от этого пользователя 5 звёзд
            all_reviews = Review.objects.filter(from_user=from_user)
            if all_reviews.exists():
                avg_rating = all_reviews.aggregate(avg=Avg('rating'))['avg']
                if avg_rating and avg_rating >= 4.8:
                    return True, "Подозрительная активность: новый аккаунт, только высокие оценки"
        
        return False, ""
    
    @classmethod
    def check_suspicious_timing(cls, from_user: User, deal) -> Tuple[bool, str]:
        """
        Проверка на подозрительное время отзыва.
        Отзыв сразу после завершения сделки может быть накруткой.
        """
        if deal.confirmed_at:
            time_since_completion = timezone.now() - deal.confirmed_at
            if time_since_completion.total_seconds() < 60:  # Менее минуты
                return True, "Слишком быстрый отзыв после завершения сделки"
        
        return False, ""
    
    @classmethod
    def run_all_checks(
        cls, 
        from_user: User, 
        to_user: User, 
        deal, 
        rating: int,
        request=None
    ) -> Tuple[bool, str, list]:
        """
        Запуск всех проверок.
        Returns: (should_block, reason, warnings)
        """
        config = RatingConfig.get_config()
        ip_address = cls.get_client_ip(request)
        user_agent = cls.get_user_agent(request)
        
        warnings = []
        
        # Критические проверки (блокируют)
        is_violation, reason = cls.check_rate_limit(from_user, config)
        if is_violation:
            cls._log_fraud(
                from_user, to_user, 'rate_limit', 
                reason, ip_address, user_agent, blocked=True
            )
            return True, reason, warnings
        
        # Проверки с предупреждением
        checks = [
            (cls.check_ip_duplicate, (from_user, to_user, ip_address), 'ip_duplicate'),
            (cls.check_circular_rating, (from_user, to_user, config), 'circular_rating'),
            (cls.check_new_account_spam, (from_user, rating, config), 'new_account_spam'),
            (cls.check_suspicious_timing, (from_user, deal), 'suspicious_timing'),
        ]
        
        for check_func, args, action_type in checks:
            is_suspicious, warning = check_func(*args)
            if is_suspicious:
                warnings.append(warning)
                cls._log_fraud(
                    from_user, to_user, action_type,
                    warning, ip_address, user_agent, blocked=False
                )
        
        return False, "", warnings
    
    @staticmethod
    def _log_fraud(
        from_user: User,
        to_user: User,
        action_type: str,
        details: str,
        ip_address: Optional[str],
        user_agent: str,
        blocked: bool
    ):
        """Записать лог о подозрительной активности"""
        RatingProtectionLog.objects.create(
            user=from_user,
            target_user=to_user,
            action_type=action_type,
            details={'message': details},
            ip_address=ip_address,
            user_agent=user_agent,
            blocked=blocked
        )


class RatingService:
    """
    Централизованный сервис расчёта рейтинга.
    Реализует взвешенный расчёт с учётом времени и достоверности отзывов.
    """
    
    @staticmethod
    def calculate_review_weight(review: Review, config: RatingConfig) -> Decimal:
        """
        Рассчитать вес отзыва.
        Учитывает:
        - Давность отзыва (новые важнее)
        - Верификацию автора отзыва
        """
        weight = Decimal('1.0')
        
        # Вес за давность (экспоненциальное затухание)
        days_old = (timezone.now() - review.created_at).days
        recency_factor = Decimal(str(max(0.5, 1.0 - (days_old / 365) * float(config.recency_weight))))
        weight *= recency_factor
        
        # Вес за верификацию автора
        if hasattr(review.from_user, 'is_verified') and review.from_user.is_verified:
            weight *= config.verified_user_weight
        
        return weight
    
    @classmethod
    def calculate_weighted_rating(cls, user: User) -> Tuple[Decimal, int]:
        """
        Рассчитать взвешенный рейтинг пользователя.
        Returns: (rating, count)
        """
        reviews = Review.objects.filter(to_user=user).select_related('from_user')
        
        if not reviews.exists():
            return Decimal('0.0'), 0
        
        config = RatingConfig.get_config()
        
        total_weighted_sum = Decimal('0.0')
        total_weight = Decimal('0.0')
        count = 0
        
        for review in reviews:
            weight = cls.calculate_review_weight(review, config)
            total_weighted_sum += Decimal(str(review.rating)) * weight
            total_weight += weight
            count += 1
        
        if total_weight > 0:
            weighted_rating = total_weighted_sum / total_weight
            # Округляем до 2 знаков
            weighted_rating = round(weighted_rating, 2)
        else:
            weighted_rating = Decimal('0.0')
        
        return weighted_rating, count
    
    @classmethod
    @transaction.atomic
    def recalculate_rating(
        cls, 
        user: User, 
        review: Optional[Review] = None,
        reason: str = 'review_added',
        triggered_by: Optional[User] = None
    ) -> Decimal:
        """
        Атомарный пересчёт рейтинга с логированием.
        """
        old_rating = user.rating
        old_count = getattr(user, 'rating_count', 0)
        
        new_rating, new_count = cls.calculate_weighted_rating(user)
        
        # Обновляем пользователя
        user.rating = new_rating
        if hasattr(user, 'rating_count'):
            user.rating_count = new_count
        if hasattr(user, 'rating_updated_at'):
            user.rating_updated_at = timezone.now()
        user.save(update_fields=['rating'] + 
                  (['rating_count'] if hasattr(user, 'rating_count') else []) +
                  (['rating_updated_at'] if hasattr(user, 'rating_updated_at') else []))
        
        # Логируем изменение
        RatingHistory.objects.create(
            user=user,
            old_rating=old_rating,
            new_rating=new_rating,
            old_count=old_count,
            new_count=new_count,
            review=review,
            reason=reason,
            created_by=triggered_by
        )
        
        return new_rating
    
    @classmethod
    def get_user_rating_details(cls, user: User) -> dict:
        """
        Получить детальную информацию о рейтинге пользователя.
        """
        reviews = Review.objects.filter(to_user=user)
        
        # Распределение оценок
        distribution = {i: 0 for i in range(1, 6)}
        for review in reviews:
            distribution[review.rating] += 1
        
        # Статистика
        total_count = reviews.count()
        
        return {
            'rating': float(user.rating),
            'total_reviews': total_count,
            'distribution': distribution,
            'rating_updated_at': getattr(user, 'rating_updated_at', None),
            'is_verified': getattr(user, 'is_verified', False),
        }
    
    @classmethod
    def get_analytics(cls, days: int = 30) -> dict:
        """
        Получить аналитику по системе рейтинга (для админов).
        """
        since = timezone.now() - timedelta(days=days)
        
        # Общая статистика
        total_reviews = Review.objects.filter(created_at__gte=since).count()
        avg_rating = Review.objects.filter(created_at__gte=since).aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        
        # Статистика блокировок
        blocked_attempts = RatingProtectionLog.objects.filter(
            created_at__gte=since,
            blocked=True
        ).count()
        
        suspicious_attempts = RatingProtectionLog.objects.filter(
            created_at__gte=since,
            blocked=False
        ).count()
        
        # Топ пользователей по рейтингу
        top_users = User.objects.filter(
            rating__gt=0
        ).order_by('-rating')[:10].values('id', 'username', 'rating', 'role')
        
        # Распределение по типам нарушений
        fraud_distribution = RatingProtectionLog.objects.filter(
            created_at__gte=since
        ).values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'total_reviews': total_reviews,
            'average_rating': round(float(avg_rating), 2),
            'blocked_attempts': blocked_attempts,
            'suspicious_attempts': suspicious_attempts,
            'top_users': list(top_users),
            'fraud_distribution': list(fraud_distribution),
        }
