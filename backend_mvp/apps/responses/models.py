from django.db import models
from django.conf import settings
from apps.orders.models import Order

class Response(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='responses')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'worker')

    def __str__(self):
        return f"Response to {self.order.title} by {self.worker.username}"
