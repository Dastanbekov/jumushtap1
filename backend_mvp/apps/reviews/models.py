from django.db import models
from django.conf import settings
from apps.deals.models import Deal


class Review(models.Model):
    """
    User review after a completed deal.
    Rating calculation is handled by RatingService.
    """
    deal = models.OneToOneField(Deal, on_delete=models.CASCADE)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='reviews_given', 
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='reviews_received', 
        on_delete=models.CASCADE
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    
    # Metadata for fraud detection
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['to_user', '-created_at']),
            models.Index(fields=['from_user', '-created_at']),
        ]

    def __str__(self):
        return f"Review from {self.from_user} to {self.to_user}: {self.rating}/5"
