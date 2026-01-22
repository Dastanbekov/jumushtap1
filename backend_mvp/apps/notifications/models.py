from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, default="Notification")
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: link to object
    # content_type, object_id ... for MVP just text is enough, or maybe a dedicated strict link?
    # Let's keep it simple.

    def __str__(self):
        return f"To {self.user}: {self.title}"


class NotificationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Toggles
    new_shift_nearby = models.BooleanField(default=True, help_text="Notify when a new shift appears nearby")
    deal_status_changed = models.BooleanField(default=True)
    payment_received = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings: {self.user}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_notification_settings(sender, instance, created, **kwargs):
    if created:
        NotificationSettings.objects.create(user=instance)
