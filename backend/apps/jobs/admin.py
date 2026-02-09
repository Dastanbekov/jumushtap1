"""
Django Admin configuration for Jobs app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Job, JobApplication, CheckIn, JobStatus, ApplicationStatus


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """
    Admin interface for Job model.
    """
    list_display = [
        'title',
        'business_name',
        'job_type',
        'date',
        'start_time',
        'workers_accepted',
        'workers_needed',
        'hourly_rate',
        'status',
        'published_at',
    ]
    list_filter = ['status', 'job_type', 'date', 'created_at']
    search_fields = ['title', 'description', 'business__business_profile__company_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'published_at', 'workers_accepted']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('id', 'business', 'job_type', 'title', 'description')
        }),
        (_('Schedule'), {
            'fields': ('date', 'start_time', 'end_time')
        }),
        (_('Payment'), {
            'fields': ('hourly_rate',)
        }),
        (_('Capacity'), {
            'fields': ('workers_needed', 'workers_accepted')
        }),
        (_('Location'), {
            'fields': (
                'location_name',
                'location_address',
                'location_lat',
                'location_lng'
            )
        }),
        (_('Requirements'), {
            'fields': ('requirements',)
        }),
        (_('Status'), {
            'fields': ('status', 'published_at')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def business_name(self, obj):
        """Get business company name."""
        try:
            return obj.business.business_profile.company_name
        except AttributeError:
            return obj.business.phone
    business_name.short_description = 'Business'
    
    actions = ['publish_jobs', 'cancel_jobs']
    
    def publish_jobs(self, request, queryset):
        """Bulk publish jobs."""
        count = 0
        for job in queryset.filter(status=JobStatus.DRAFT):
            try:
                job.transition_to(JobStatus.PUBLISHED)
                count += 1
            except ValueError:
                pass
        
        self.message_user(request, f'{count} job(s) published.')
    publish_jobs.short_description = "Publish selected jobs"
    
    def cancel_jobs(self, request, queryset):
        """Bulk cancel jobs."""
        count = 0
        for job in queryset.exclude(status__in=[JobStatus.COMPLETED, JobStatus.CANCELLED]):
            try:
                job.transition_to(JobStatus.CANCELLED)
                count += 1
            except ValueError:
                pass
        
        self.message_user(request, f'{count} job(s) cancelled.')
    cancel_jobs.short_description = "Cancel selected jobs"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for JobApplication model.
    """
    list_display = [
        'worker_name',
        'job_title',
        'business_name',
        'status',
        'applied_at',
        'responded_at',
    ]
    list_filter = ['status', 'applied_at']
    search_fields = [
        'worker__worker_profile__full_name',
        'job__title',
        'job__business__business_profile__company_name'
    ]
    readonly_fields = ['id', 'applied_at', 'responded_at']
    
    fieldsets = (
        (_('Application'), {
            'fields': ('id', 'job', 'worker', 'status', 'message')
        }),
        (_('Timestamps'), {
            'fields': ('applied_at', 'responded_at')
        }),
    )
    
    def worker_name(self, obj):
        try:
            return obj.worker.worker_profile.full_name
        except AttributeError:
            return obj.worker.phone
    worker_name.short_description = 'Worker'
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job'
    
    def business_name(self, obj):
        try:
            return obj.job.business.business_profile.company_name
        except AttributeError:
            return obj.job.business.phone
    business_name.short_description = 'Business'
    
    actions = ['accept_applications', 'reject_applications']
    
    def accept_applications(self, request, queryset):
        """Bulk accept applications."""
        count = 0
        for app in queryset.filter(status=ApplicationStatus.PENDING):
            try:
                if not app.job.is_full:
                    app.accept()
                    count += 1
            except ValueError:
                pass
        
        self.message_user(request, f'{count} application(s) accepted.')
    accept_applications.short_description = "Accept selected applications"
    
    def reject_applications(self, request, queryset):
        """Bulk reject applications."""
        count = 0
        for app in queryset.filter(status=ApplicationStatus.PENDING):
            try:
                app.reject()
                count += 1
            except ValueError:
                pass
        
        self.message_user(request, f'{count} application(s) rejected.')
    reject_applications.short_description = "Reject selected applications"


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    """
    Admin interface for CheckIn model.
    """
    list_display = [
        'worker_name',
        'job_title',
        'checked_in_at',
        'checked_out_at',
        'worked_hours_display',
        'is_checked_out',
    ]
    list_filter = ['checked_in_at']
    search_fields = [
        'application__worker__worker_profile__full_name',
        'application__job__title'
    ]
    readonly_fields = [
        'id',
        'checked_in_at',
        'checked_out_at',
        'worked_hours',
        'created_at'
    ]
    
    fieldsets = (
        (_('Application'), {
            'fields': ('id', 'application')
        }),
        (_('Check-in'), {
            'fields': ('checked_in_at', 'check_in_lat', 'check_in_lng')
        }),
        (_('Check-out'), {
            'fields': ('checked_out_at', 'check_out_lat', 'check_out_lng')
        }),
        (_('Stats'), {
            'fields': ('worked_hours', 'is_checked_out')
        }),
        (_('Device Info'), {
            'fields': ('device_info',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def worker_name(self, obj):
        try:
            return obj.application.worker.worker_profile.full_name
        except AttributeError:
            return obj.application.worker.phone
    worker_name.short_description = 'Worker'
    
    def job_title(self, obj):
        return obj.application.job.title
    job_title.short_description = 'Job'
    
    def worked_hours_display(self, obj):
        if obj.worked_hours:
            return f"{obj.worked_hours:.2f}h"
        return "-"
    worked_hours_display.short_description = 'Worked Hours'
    
    def has_add_permission(self, request):
        """Prevent manual check-in creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent check-in modification."""
        return False
