from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('worker', 'Worker'),
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Rating fields
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_count = models.PositiveIntegerField(default=0, help_text="Total number of reviews received")
    rating_updated_at = models.DateTimeField(null=True, blank=True, help_text="Last rating update timestamp")
    
    # Verification status
    is_verified = models.BooleanField(default=False, help_text="Verified account (trusted reviews)")
    
    # Status can be 'active', 'blocked'
    status = models.CharField(max_length=20, default='active')

    class Meta:
        indexes = [
            models.Index(fields=['-rating']),
            models.Index(fields=['role', '-rating']),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"
