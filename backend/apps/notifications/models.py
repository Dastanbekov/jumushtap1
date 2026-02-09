"""
Models for Notifications app.
Manages FCM devices and notification history.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.users.models import CustomUser


class Device(models.Model):
    """
    User device for push notifications (FCM).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name=_('User')
    )
    
    registration_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('FCM Token'),
        help_text=_('Firebase Cloud Messaging registration token')
    )
    
    device_type = models.CharField(
        max_length=20,
        choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
        default='android',
        verbose_name=_('Device Type')
    )
    
    active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Inactive devices are skipped')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        ordering = ['-last_used_at']
        indexes = [
            models.Index(fields=['user', 'active']),
            models.Index(fields=['registration_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.device_type} ({self.registration_id[:8]}...)"


class Notification(models.Model):
    """
    Notification history log.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User')
    )
    
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    body = models.TextField(verbose_name=_('Body'))
    
    # Additional data for deep linking (JSON)
    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Data'),
        help_text=_('Custom data payload for the notification')
    )
    
    is_read = models.BooleanField(default=False, verbose_name=_('Read'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user}: {self.title}"
