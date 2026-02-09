"""
Admin configuration for Notifications app.
"""

from django.contrib import admin
from .models import Device, Notification
from .services import NotificationService


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_type', 'is_active_badge', 'last_used_at', 'created_at']
    list_filter = ['device_type', 'active', 'last_used_at']
    search_fields = ['user__phone', 'registration_id']
    
    def is_active_badge(self, obj):
        return "✅" if obj.active else "❌"
    is_active_badge.short_description = "Active"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__phone', 'title', 'body']
    readonly_fields = ['created_at']
    
    actions = ['resend_notification']
    
    def resend_notification(self, request, queryset):
        count = 0
        for notif in queryset:
            try:
                NotificationService.send_notification(
                    user=notif.user,
                    title=notif.title,
                    body=notif.body,
                    data=notif.data
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f"Resent {count} notifications.")
    resend_notification.short_description = "Resend selected notifications"
