from django.db import models
from apps.deals.models import Deal

class Contract(models.Model):
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE, related_name='contract')
    file = models.FileField(upload_to='contracts/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contract for Deal {self.deal.id}"
