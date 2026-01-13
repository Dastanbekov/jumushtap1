from django.db import models
from django.conf import settings
from apps.orders.models import Order

class Deal(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('waiting_confirm', 'Completed (Waiting Confirmation)'),
        ('finished', 'Finished'),
        ('dispute', 'Dispute'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='deal')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_deals')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worker_deals')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    
    worker_confirmed = models.BooleanField(default=False)
    customer_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Deal: {self.order.title}"
