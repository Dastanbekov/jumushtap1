from django.db import models
from django.conf import settings
from apps.deals.models import Deal

class PayoutLog(models.Model):
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending') # simulated
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout {self.amount} to {self.worker}"
