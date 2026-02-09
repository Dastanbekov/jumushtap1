"""
Models for Jobs/Shifts management.
Implements state machine, geolocation, and business logic per MVP spec.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField

from apps.users.models import CustomUser


class JobType(models.TextChoices):
    """Types of jobs available in the platform."""
    WAITER = 'waiter', _('Waiter')
    COURIER = 'courier', _('Courier')
    LOADER = 'loader', _('Loader')
    CLEANER = 'cleaner', _('Cleaner')
    CASHIER = 'cashier', _('Cashier')
    BARTENDER = 'bartender', _('Bartender')
    COOK = 'cook', _('Cook')
    SECURITY = 'security', _('Security Guard')
    PROMOTER = 'promoter', _('Promoter')
    OTHER = 'other', _('Other')


class JobStatus(models.TextChoices):
    """
    Job lifecycle states.
    Implements state machine transitions.
    """
    DRAFT = 'draft', _('Draft')
    PUBLISHED = 'published', _('Published')
    IN_PROGRESS = 'in_progress', _('In Progress')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')


class ApplicationStatus(models.TextChoices):
    """Worker application status."""
    PENDING = 'pending', _('Pending')
    ACCEPTED = 'accepted', _('Accepted')
    REJECTED = 'rejected', _('Rejected')
    WITHDRAWN = 'withdrawn', _('Withdrawn')


class Job(models.Model):
    """
    Shift/Job posting model.
    Created by business, applied to by workers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Business owner
    business = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
        limit_choices_to={'user_type': 'business'},
        verbose_name=_('Business')
    )
    
    # Job details
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        verbose_name=_('Job Type')
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_('Job Title'),
        help_text=_('Short descriptive title')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed job description and requirements')
    )
    
    # Schedule
    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Start Time'))
    end_time = models.TimeField(verbose_name=_('End Time'))
    
    # Payment
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Hourly Rate'),
        help_text=_('Payment per hour in local currency')
    )
    
    # Capacity
    workers_needed = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name=_('Workers Needed')
    )
    workers_accepted = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Workers Accepted')
    )
    
    # Location
    location_name = models.CharField(
        max_length=255,
        verbose_name=_('Location Name'),
        help_text=_('e.g., "Main Office", "Restaurant Branch 1"')
    )
    location_address = models.CharField(
        max_length=500,
        verbose_name=_('Address')
    )
    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Latitude')
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Longitude')
    )
    
    # Requirements
    requirements = models.TextField(
        blank=True,
        verbose_name=_('Requirements'),
        help_text=_('Skills, experience, or other requirements')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
        verbose_name=_('Status')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['business', 'status']),
            models.Index(fields=['date', 'start_time']),
            models.Index(fields=['location_lat', 'location_lng']),
            models.Index(fields=['job_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.date} at {self.start_time})"
    
    def can_transition_to(self, new_status):
        """
        Check if status transition is allowed (state machine).
        
        Allowed transitions:
        - draft → published, cancelled
        - published → in_progress, cancelled
        - in_progress → completed, cancelled
        - completed, cancelled → (final states, no transitions)
        """
        valid_transitions = {
            JobStatus.DRAFT: [JobStatus.PUBLISHED, JobStatus.CANCELLED],
            JobStatus.PUBLISHED: [JobStatus.IN_PROGRESS, JobStatus.CANCELLED],
            JobStatus.IN_PROGRESS: [JobStatus.COMPLETED, JobStatus.CANCELLED],
            JobStatus.COMPLETED: [],
            JobStatus.CANCELLED: [],
        }
        
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status):
        """
        Transition to new status with validation.
        Raises ValueError if transition is invalid.
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        
        old_status = self.status
        self.status = new_status
        
        # Set published_at timestamp
        if new_status == JobStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        self.save(update_fields=['status', 'updated_at', 'published_at'])
        
        return old_status, new_status
    
    @property
    def is_full(self):
        """Check if all worker slots are filled."""
        return self.workers_accepted >= self.workers_needed
    
    @property
    def available_slots(self):
        """Number of available worker slots."""
        return max(0, self.workers_needed - self.workers_accepted)
    
    @property
    def duration_hours(self):
        """Calculate job duration in hours."""
        from datetime import datetime, timedelta
        
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        
        # Handle overnight shifts
        if end < start:
            end += timedelta(days=1)
        
        duration = end - start
        return duration.total_seconds() / 3600
    
    @property
    def total_cost(self):
        """Calculate total cost for all workers."""
        return self.hourly_rate * self.duration_hours * self.workers_needed


class JobApplication(models.Model):
    """
    Worker's application to a job.
    One worker can apply to one job only once.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('Job')
    )
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='job_applications',
        limit_choices_to={'user_type': 'worker'},
        verbose_name=_('Worker')
    )
    
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        verbose_name=_('Status')
    )
    
    # Optional message from worker
    message = models.TextField(
        blank=True,
        verbose_name=_('Application Message'),
        help_text=_('Optional message from worker to business')
    )
    
    # Timestamps
    applied_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Job Application')
        verbose_name_plural = _('Job Applications')
        ordering = ['-applied_at']
        unique_together = [('job', 'worker')]
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['worker', 'status']),
            models.Index(fields=['-applied_at']),
        ]
    
    def __str__(self):
        return f"{self.worker} → {self.job.title} ({self.status})"
    
    def accept(self, by_user=None):
        """
        Accept application.
        Increments job's workers_accepted counter.
        """
        if self.status != ApplicationStatus.PENDING:
            raise ValueError("Only pending applications can be accepted")
        
        if self.job.is_full:
            raise ValueError("Job is already full")
        
        self.status = ApplicationStatus.ACCEPTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
        # Increment accepted workers count
        Job.objects.filter(id=self.job.id).update(
            workers_accepted=models.F('workers_accepted') + 1
        )
        
        self.job.refresh_from_db()
        
        return self
    
    def reject(self):
        """Reject application."""
        if self.status != ApplicationStatus.PENDING:
            raise ValueError("Only pending applications can be rejected")
        
        self.status = ApplicationStatus.REJECTED
        self.responded_at = timezone.now()
        self.save(update_fields=['status', 'responded_at'])
        
        return self
    
    def withdraw(self):
        """Worker withdraws application."""
        if self.status == ApplicationStatus.ACCEPTED:
            # Decrement accepted workers count
            Job.objects.filter(id=self.job.id).update(
                workers_accepted=models.F('workers_accepted') - 1
            )
        
        self.status = ApplicationStatus.WITHDRAWN
        self.save(update_fields=['status'])
        
        return self


class CheckIn(models.Model):
    """
    Check-in/Check-out tracking for workers.
    Validates GPS location and tracks actual work time.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='checkin',
        verbose_name=_('Application')
    )
    
    # Check-in
    checked_in_at = models.DateTimeField(verbose_name=_('Checked In At'))
    check_in_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Check-in Latitude')
    )
    check_in_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_('Check-in Longitude')
    )
    
    # Check-out
    checked_out_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Checked Out At')
    )
    check_out_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Check-out Latitude')
    )
    check_out_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Check-out Longitude')
    )
    
    # Device info for fraud detection
    device_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Device Info'),
        help_text=_('Device metadata for anti-fraud')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Check-in')
        verbose_name_plural = _('Check-ins')
        ordering = ['-checked_in_at']
        indexes = [
            models.Index(fields=['-checked_in_at']),
            models.Index(fields=['application']),
        ]
    
    def __str__(self):
        status = 'Checked out' if self.checked_out_at else 'Checked in'
        return f"{self.application.worker} - {self.application.job.title} ({status})"
    
    def checkout(self, lat, lng, device_info=None):
        """
        Perform check-out.
        
        Args:
            lat: Checkout latitude
            lng: Checkout longitude
            device_info: Optional device metadata
        """
        if self.checked_out_at:
            raise ValueError("Already checked out")
        
        self.checked_out_at = timezone.now()
        self.check_out_lat = lat
        self.check_out_lng = lng
        
        if device_info:
            self.device_info.update(device_info)
        
        self.save(update_fields=[
            'checked_out_at',
            'check_out_lat',
            'check_out_lng',
            'device_info'
        ])
        
        return self
    
    @property
    def worked_hours(self):
        """Calculate actual worked hours."""
        if not self.checked_out_at:
            return None
        
        duration = self.checked_out_at - self.checked_in_at
        return duration.total_seconds() / 3600
    
    @property
    def is_checked_out(self):
        """Check if worker has checked out."""
        return self.checked_out_at is not None
