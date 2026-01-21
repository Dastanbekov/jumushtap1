from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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



class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name


class WorkerProfile(models.Model):
    """
    Profile for Workers (Performers).
    Stores KYC data, experience, and skills.
    """
    VERIFICATION_STATUS = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending Approval'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    
    # KYC Data
    birth_date = models.DateField(null=True, blank=True)
    passport_series = models.CharField(max_length=10, blank=True, null=True) # Should be encrypted in PROD
    passport_number = models.CharField(max_length=20, blank=True, null=True)
    passport_scan_front = models.ImageField(upload_to='kyc/passports/', blank=True, null=True)
    passport_scan_back = models.ImageField(upload_to='kyc/passports/', blank=True, null=True)
    
    # Professional Data
    about = models.TextField(blank=True, help_text="Short bio")
    experience_years = models.PositiveIntegerField(default=0)
    skills = models.ManyToManyField(Skill, blank=True)
    
    # Status
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='unverified')
    rejection_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Worker Profile: {self.user.username}"


class CustomerProfile(models.Model):
    """
    Profile for Business Customers.
    Stores KYB data (INN, company info).
    """
    VERIFICATION_STATUS = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending Approval'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    
    # Company Data
    company_name = models.CharField(max_length=255, blank=True)
    inn = models.CharField(max_length=20, blank=True, help_text="Tax Identification Number")
    legal_address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company/logos/', blank=True, null=True)
    
    # Status
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='unverified')
    rejection_reason = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Customer Profile: {self.company_name or self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create profile based on role.
    """
    if created:
        if instance.role == 'worker':
            WorkerProfile.objects.create(user=instance)
        elif instance.role == 'customer':
            CustomerProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save profile when user is saved.
    """
    if instance.role == 'worker' and hasattr(instance, 'worker_profile'):
        instance.worker_profile.save()
    elif instance.role == 'customer' and hasattr(instance, 'customer_profile'):
        instance.customer_profile.save()
