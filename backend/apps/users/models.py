from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from .managers import CustomUserManager
import secrets


class UserType(models.TextChoices):
    WORKER = 'worker', _('Worker')
    BUSINESS = 'business', _('Business')
    ADMIN = 'admin', _(('Admin'))


class VerificationStatus(models.TextChoices):
    UNVERIFIED = 'unverified', _('Unverified')
    PENDING = 'pending', _('Pending Review')
    VERIFIED = 'verified', _('Verified')
    REJECTED = 'rejected', _('Rejected')


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for JumushTap.
    Uses phone number as primary identifier (no email/password for MVP).
    """
    phone = PhoneNumberField(unique=True, verbose_name=_('Phone Number'))
    user_type = models.CharField(
        max_length=20, 
        choices=UserType.choices,
        verbose_name=_('User Type')
    )
   
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['user_type']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['user_type']),
        ]

    def __str__(self):
        return f"{self.phone} ({self.user_type})"

    @property
    def is_worker(self):
        return self.user_type == UserType.WORKER

    @property
    def is_business(self):
        return self.user_type == UserType.BUSINESS


class OTP(models.Model):
    """
    One-Time Password model for SMS authentication.
    Implements security best practices: expiration, single-use, rate limiting.
    """
    phone = PhoneNumberField(db_index=True, verbose_name=_('Phone Number'))
    code = models.CharField(max_length=6, verbose_name=_('OTP Code'))
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name=_('Expires At'))
    is_used = models.BooleanField(default=False, verbose_name=_('Is Used'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Is Verified'))
    
    class Meta:
        verbose_name = _('OTP')
        verbose_name_plural = _('OTPs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', '-created_at']),
            models.Index(fields=['code', 'phone']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone} - {'Used' if self.is_used else 'Active'}"
    
    @classmethod
    def generate_code(cls):
        """Generate secure 6-digit OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    def is_valid(self):
        """Check if OTP is still valid (not expired, not used)."""
        return (
            not self.is_used and 
            timezone.now() < self.expires_at
        )
    
    def mark_as_used(self):
        """Mark OTP as used and verified."""
        self.is_used = True
        self.is_verified = True
        self.save(update_fields=['is_used', 'is_verified'])


class WorkerProfile(models.Model):
    """
    Profile for Workers (исполнители).
    MVP fields per technical specification.
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='worker_profile'
    )
    full_name = models.CharField(max_length=255, verbose_name=_('Full Name'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('Date of Birth'))
    photo = models.ImageField(
        upload_to='workers/photos/',
        null=True,
        blank=True,
        verbose_name=_('Photo (Selfie)')
    )
    
    # Skills and experience (JSON for flexibility)
    skills = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Skills'),
        help_text=_('Array of skill tags, e.g., ["waiter", "courier"]')
    )
    experience = models.TextField(
        blank=True,
        verbose_name=_('Experience'),
        help_text=_('Text description of work experience')
    )
    
    # Performance metrics
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Rating'),
        help_text=_('Average rating from 0.00 to 5.00')
    )
    completed_jobs_count = models.IntegerField(
        default=0,
        verbose_name=_('Completed Jobs Count')
    )
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        verbose_name=_('Verification Status')
    )
    
    # Payment info
    payment_account_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Payment Account ID'),
        help_text=_('ID from payment service provider for payouts')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Worker Profile')
        verbose_name_plural = _('Worker Profiles')
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['-rating']),
        ]

    def __str__(self):
        return f"Worker: {self.full_name} ({self.verification_status})"
    
    def update_rating(self):
        """
        Update average rating from all ratings.
        """
        from django.db.models import Avg
        from apps.ratings.models import Rating
        
        avg_rating = Rating.objects.filter(
            reviewee=self.user
        ).aggregate(Avg('score'))['score__avg']
        
        if avg_rating is not None:
            self.rating = round(avg_rating, 2)
            self.save(update_fields=['rating'])


class BusinessProfile(models.Model):
    """
    Profile for Business (заказчики/бизнес).
    MVP fields per technical specification.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='business_profile'
    )
    company_name = models.CharField(max_length=255, verbose_name=_('Company Name'))
    bin = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('BIN'),
        help_text=_('Business Identification Number')
    )
    inn = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('INN'),
        help_text=_('Individual Identification Number')
    )
    legal_address = models.TextField(verbose_name=_('Legal Address'))
    contact_name = models.CharField(max_length=255, verbose_name=_('Contact Person Name'))
    contact_number = PhoneNumberField(verbose_name=_('Contact Phone Number'))
    
    # Documents (S3 URLs stored as JSON array)
    documents = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Documents'),
        help_text=_('Array of document objects: [{type, url, uploaded_at}]')
    )
    
    # Multiple locations (JSON array of addresses)
    locations = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Locations'),
        help_text=_('Array of location objects: [{address, lat, lng, name}]')
    )
    
    # Rating
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Rating')
    )
    
    def update_rating(self):
        """
        Update average rating from all ratings.
        """
        from django.db.models import Avg
        from apps.ratings.models import Rating
        
        avg_rating = Rating.objects.filter(
            reviewee=self.user
        ).aggregate(Avg('score'))['score__avg']
        
        if avg_rating is not None:
            self.rating = round(avg_rating, 2)
            self.save(update_fields=['rating'])
    
    # Verification
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        verbose_name=_('Verification Status')
    )
    verification_notes = models.TextField(
        blank=True,
        verbose_name=_('Admin Verification Notes')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Business Profile')
        verbose_name_plural = _('Business Profiles')
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['company_name']),
        ]

    def __str__(self):
        return f"Business: {self.company_name} ({self.verification_status})"
    
    def add_location(self, address, lat, lng, name=None):
        """Helper method to add a location to the business."""
        location = {
            'address': address,
            'lat': float(lat),
            'lng': float(lng),
            'name': name or address,
            'added_at': timezone.now().isoformat(),
        }
        self.locations.append(location)
        self.save(update_fields=['locations'])
        return location
    
    def add_document(self, document_type, url):
        """Helper method to add a document."""
        document = {
            'type': document_type,
            'url': url,
            'uploaded_at': timezone.now().isoformat(),
        }
        self.documents.append(document)
        self.save(update_fields=['documents'])
        return document


class Statistics(CustomUser):
    """
    System Statistics proxy model.
    """
    class Meta:
        proxy = True
        verbose_name = 'System Statistic'
        verbose_name_plural = 'System Statistics'
