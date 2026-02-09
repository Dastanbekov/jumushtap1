"""
Django Admin configuration for payments app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import Transaction, Escrow, Payout, TransactionStatus, EscrowStatus, PayoutStatus


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for Transaction model.
    """
    list_display = [
        'id',
        'job_title',
        'business_name',
        'worker_name',
        'amount',
        'platform_fee',
        'worker_payout',
        'status_badge',
        'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'id',
        'job__title',
        'business__business_profile__company_name',
        'worker__worker_profile__full_name',
        'payment_intent_id',
    ]
    readonly_fields = [
        'id',
        'idempotency_key',
        'payment_intent_id',
        'created_at',
        'updated_at',
        'completed_at',
    ]
    
    fieldsets = (
        (_('Transaction'), {
            'fields': ('id', 'job', 'business', 'worker', 'status')
        }),
        (_('Amounts'), {
            'fields': ('amount', 'platform_fee', 'worker_payout')
        }),
        (_('PSP Integration'), {
            'fields': ('payment_intent_id', 'idempotency_key')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job'
    
    def business_name(self, obj):
        try:
            return obj.business.business_profile.company_name
        except AttributeError:
            return obj.business.phone
    business_name.short_description = 'Business'
    
    def worker_name(self, obj):
        try:
            return obj.worker.worker_profile.full_name
        except AttributeError:
            return obj.worker.phone
    worker_name.short_description = 'Worker'
    
    def status_badge(self, obj):
        colors = {
            TransactionStatus.PENDING: 'gray',
            TransactionStatus.HELD: 'orange',
            TransactionStatus.COMPLETED: 'green',
            TransactionStatus.REFUNDED: 'blue',
            TransactionStatus.FAILED: 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    """
    Admin interface for Escrow model.
    """
    list_display = [
        'id',
        'job_title',
        'held_amount',
        'status_badge',
        'held_at',
        'released_at',
        'auto_release_hours',
    ]
    list_filter = ['status', 'held_at']
    search_fields = [
        'id',
        'application__job__title',
        'transaction__id',
    ]
    readonly_fields = ['id', 'held_at', 'released_at']
    
    fieldsets = (
        (_('Escrow'), {
            'fields': ('id', 'transaction', 'application', 'held_amount', 'status')
        }),
        (_('Configuration'), {
            'fields': ('auto_release_hours',)
        }),
        (_('Timestamps'), {
            'fields': ('held_at', 'released_at')
        }),
    )
    
    def job_title(self, obj):
        return obj.application.job.title
    job_title.short_description = 'Job'
    
    def status_badge(self, obj):
        colors = {
            EscrowStatus.HELD: 'orange',
            EscrowStatus.RELEASED: 'green',
            EscrowStatus.REFUNDED: 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Prevent manual escrow creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent escrow modification."""
        return False


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """
    Admin interface for Payout model.
    """
    list_display = [
        'id',
        'worker_name',
        'amount',
        'status_badge',
        'transfer_id',
        'retry_count',
        'initiated_at',
        'completed_at',
    ]
    list_filter = ['status', 'initiated_at']
    search_fields = [
        'id',
        'worker__worker_profile__full_name',
        'transfer_id',
        'transaction__id',
    ]
    readonly_fields = [
        'id',
        'transfer_id',
        'initiated_at',
        'completed_at',
        'failed_at',
    ]
    
    fieldsets = (
        (_('Payout'), {
            'fields': ('id', 'transaction', 'worker', 'amount', 'status')
        }),
        (_('PSP Transfer'), {
            'fields': ('transfer_id', 'destination_account')
        }),
        (_('Error Handling'), {
            'fields': ('failure_reason', 'retry_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('initiated_at', 'completed_at', 'failed_at')
        }),
    )
    
    def worker_name(self, obj):
        try:
            return obj.worker.worker_profile.full_name
        except AttributeError:
            return obj.worker.phone
    worker_name.short_description = 'Worker'
    
    def status_badge(self, obj):
        colors = {
            PayoutStatus.PENDING: 'gray',
            PayoutStatus.PROCESSING: 'orange',
            PayoutStatus.COMPLETED: 'green',
            PayoutStatus.FAILED: 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['retry_failed_payouts']
    
    def retry_failed_payouts(self, request, queryset):
        """Retry failed payouts (manual trigger)."""
        failed = queryset.filter(status=PayoutStatus.FAILED, retry_count__lt=3)
        count = 0
        
        for payout in failed:
            # TODO: Implement retry logic
            self.message_user(request, f'Retry would be triggered for {payout.id}')
            count += 1
        
        self.message_user(request, f'{count} payout(s) queued for retry.')
    retry_failed_payouts.short_description = "Retry failed payouts"
    
    def has_add_permission(self, request):
        """Prevent manual payout creation."""
        return False
