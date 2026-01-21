from django.contrib import admin
from .models import RatingHistory, RatingProtectionLog, RatingConfig


@admin.register(RatingHistory)
class RatingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'old_rating', 'new_rating', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['user', 'old_rating', 'new_rating', 'old_count', 'new_count', 
                       'review', 'reason', 'details', 'created_at', 'created_by']


@admin.register(RatingProtectionLog)
class RatingProtectionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action_type', 'blocked', 'ip_address', 'created_at']
    list_filter = ['action_type', 'blocked', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'target_user', 'action_type', 'details', 
                       'ip_address', 'user_agent', 'blocked', 'created_at']


@admin.register(RatingConfig)
class RatingConfigAdmin(admin.ModelAdmin):
    list_display = ['recency_weight', 'verified_user_weight', 'max_reviews_per_day', 'updated_at']
    
    def has_add_permission(self, request):
        # Singleton - только одна запись
        return not RatingConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
