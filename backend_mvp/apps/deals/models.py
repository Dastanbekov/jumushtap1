from django.db import models
from django.conf import settings
from apps.orders.models import Order
import uuid

class Deal(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'Pending Start'), # Created but work not started
        ('started', 'Working'),           # QR scanned, work is active
        ('waiting_confirm', 'Completed (Waiting Confirmation)'), # QR out scanned, waiting for manual confirm
        ('finished', 'Finished'),
        ('dispute', 'Dispute'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='deal')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_deals')
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='worker_deals')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # QR & Time Tracking
    qr_token = models.UUIDField(default=uuid.uuid4, editable=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    # Geo Check-in
    check_in_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    worker_confirmed = models.BooleanField(default=False)
    customer_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Deal: {self.order.title} ({self.status})"
