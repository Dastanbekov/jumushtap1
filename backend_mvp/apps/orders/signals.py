from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .services import MatchingService
import threading

@receiver(post_save, sender=Order)
def order_created_notification(sender, instance, created, **kwargs):
    if created and instance.status == 'open':
        # Send Push in separate thread to avoid blocking response
        threading.Thread(
            target=MatchingService.notify_nearby_workers,
            args=(instance,)
        ).start()
