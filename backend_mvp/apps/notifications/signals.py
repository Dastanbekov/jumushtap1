from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.responses.models import Response
from apps.deals.models import Deal
from .models import Notification

@receiver(post_save, sender=Response)
def notify_response_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.order.customer,
            text=f"New response to your order '{instance.order.title}'"
        )
    elif instance.status == 'accepted':
         Notification.objects.create(
            user=instance.worker,
            text=f"Your response to '{instance.order.title}' was accepted!"
        )

@receiver(post_save, sender=Deal)
def notify_deal_update(sender, instance, created, **kwargs):
    if not created and instance.status == 'finished':
        Notification.objects.create(
            user=instance.customer,
            text=f"Deal '{instance.order.title}' is finished."
        )
        Notification.objects.create(
            user=instance.worker,
            text=f"Deal '{instance.order.title}' is finished."
        )
