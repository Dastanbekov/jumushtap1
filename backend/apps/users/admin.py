"""
Django Admin configuration for Users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum

from .models import CustomUser, OTP, WorkerProfile, BusinessProfile, VerificationStatus, Statistics
from apps.jobs.models import Job, JobStatus
from apps.payments.models import Transaction, TransactionStatus


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Custom admin for CustomUser model.
    """
    list_display = ['phone', 'user_type', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        (_('Personal info'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'user_type', 'password1', 'password2'),
        }),
    )


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    """
    Hack to show statistics in Django Admin without custom templates.
    """
    change_list_template = 'admin/statistics_change_list.html'
    
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def changelist_view(self, request, extra_context=None):
        # Gather metrics
        total_users = CustomUser.objects.count()
        workers_count = CustomUser.objects.filter(user_type='worker').count()
        business_count = CustomUser.objects.filter(user_type='business').count()
        
        active_jobs = Job.objects.filter(status=JobStatus.PUBLISHED).count()
        total_jobs = Job.objects.count()
        
        total_volume = Transaction.objects.filter(status=TransactionStatus.HELD).aggregate(Sum('amount'))['amount__sum'] or 0
        
        metrics = {
            'total_users': total_users,
            'workers': workers_count,
            'businesses': business_count,
            'active_jobs': active_jobs,
            'total_jobs': total_jobs,
            'escrow_volume': float(total_volume),
        }
        
        extra_context = extra_context or {}
        extra_context['metrics'] = metrics
        extra_context['title'] = "System Statistics"
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    Admin for OTP model (read-only for security).
    """
    list_display = ['phone', 'code', 'created_at', 'expires_at', 'is_used', 'is_verified']
    list_filter = ['is_used', 'is_verified', 'created_at']
    search_fields = ['phone']
    ordering = ['-created_at']
    readonly_fields = ['phone', 'code', 'created_at', 'expires_at', 'is_used', 'is_verified']
    
    def has_add_permission(self, request):
        """Prevent manual OTP creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent OTP modification."""
        return False


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    """
    Admin for Worker profiles.
    """
    list_display = ['full_name', 'user', 'verification_status', 'rating', 'completed_jobs_count']
    list_filter = ['verification_status', 'created_at']
    search_fields = ['full_name', 'user__phone']
    readonly_fields = ['rating', 'completed_jobs_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('user', 'full_name', 'date_of_birth', 'photo')
        }),
        (_('Skills & Experience'), {
            'fields': ('skills', 'experience')
        }),
        (_('Performance'), {
            'fields': ('rating', 'completed_jobs_count')
        }),
        (_('Verification'), {
            'fields': ('verification_status',)
        }),
        (_('Payment'), {
            'fields': ('payment_account_id',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_verification', 'reject_verification']
    
    def approve_verification(self, request, queryset):
        """Bulk approve worker verification."""
        updated = queryset.update(verification_status=VerificationStatus.VERIFIED)
        self.message_user(request, f'{updated} worker(s) verified.')
    approve_verification.short_description = "Approve selected workers"
    
    def reject_verification(self, request, queryset):
        """Bulk reject worker verification."""
        updated = queryset.update(verification_status=VerificationStatus.REJECTED)
        self.message_user(request, f'{updated} worker(s) rejected.')
    reject_verification.short_description = "Reject selected workers"


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    """
    Admin for Business profiles.
    """
    list_display = ['company_name', 'user', 'bin', 'verification_status', 'created_at']
    list_filter = ['verification_status', 'created_at']
    search_fields = ['company_name', 'bin', 'inn', 'user__phone']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Basic Info'), {
            'fields': ('user', 'company_name', 'bin', 'inn')
        }),
        (_('Contact'), {
            'fields': ('legal_address', 'contact_name', 'contact_number')
        }),
        (_('Documents & Locations'), {
            'fields': ('documents', 'locations')
        }),
        (_('Verification'), {
            'fields': ('verification_status', 'verification_notes')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_verification', 'reject_verification']
    
    def approve_verification(self, request, queryset):
        """Bulk approve business verification."""
        updated = queryset.update(verification_status=VerificationStatus.VERIFIED)
        self.message_user(request, f'{updated} business(es) verified.')
    approve_verification.short_description = "Approve selected businesses"
    
    def reject_verification(self, request, queryset):
        """Bulk reject business verification."""
        updated = queryset.update(verification_status=VerificationStatus.REJECTED)
        self.message_user(request, f'{updated} business(es) rejected.')
    reject_verification.short_description = "Reject selected businesses"
