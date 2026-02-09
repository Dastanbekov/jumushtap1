"""
Models for Payment system.
Implements escrow mechanism for secure transactions.
"""

import uuid
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator

from apps.users.models import CustomUser
from apps.jobs.models import Job, JobApplication


class TransactionStatus(models.TextChoices):
    """Transaction status lifecycle."""
    PENDING = 'pending', _('Pending')
    HELD = 'held', _('Held in Escrow')
    COMPLETED = 'completed', _('Completed')
    REFUNDED = 'refunded', _('Refunded')
    FAILED = 'failed', _('Failed')


class EscrowStatus(models.TextChoices):
    """Escrow status."""
    HELD = 'held', _('Held')
    RELEASED = 'released', _('Released')
    REFUNDED = 'refunded', _('Refunded')


class PayoutStatus(models.TextChoices):
    """Payout status."""
    PENDING = 'pending', _('Pending')
    PROCESSING = 'processing', _('Processing')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')


class Transaction(models.Model):
    """
    Main payment transaction record.
    Created when business accepts worker application.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Related entities
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Job')
    )
    business = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='business_transactions',
        limit_choices_to={'user_type': 'business'},
        verbose_name=_('Business (Payer)')
    )
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='worker_transactions',
        limit_choices_to={'user_type': 'worker'},
        verbose_name=_('Worker (Payee)')
    )
    
    # Amounts
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Total Amount'),
        help_text=_('Total transaction amount')
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Platform Fee'),
        help_text=_('Commission charged by platform')
    )
    worker_payout = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Worker Payout'),
        help_text=_('Net amount paid to worker')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        verbose_name=_('Status')
    )
    
    # PSP integration
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Payment Intent ID'),
        help_text=_('PSP payment intent identifier')
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Idempotency Key'),
        help_text=_('Unique key to prevent duplicate transactions')
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional transaction data')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['business', '-created_at']),
            models.Index(fields=['worker', '-created_at']),
            models.Index(fields=['idempotency_key']),
        ]
    
    def __str__(self):
        return f"Transaction {self.id} - {self.amount} ({self.status})"
    
    def calculate_fees(self, fee_percentage=Decimal('0.10')):
        """
        Calculate platform fee and worker payout.
        Default: 10% platform fee.
        """
        self.platform_fee = self.amount * fee_percentage
        self.worker_payout = self.amount - self.platform_fee
        return self.platform_fee, self.worker_payout


class Escrow(models.Model):
    """
    Escrow record for holding funds.
    Funds are held when application is accepted.
    Released after worker checks out and job completes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='escrow',
        verbose_name=_('Transaction')
    )
    application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='escrow',
        verbose_name=_('Job Application')
    )
    
    # Escrow details
    held_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Held Amount')
    )
    
    status = models.CharField(
        max_length=20,
        choices=EscrowStatus.choices,
        default=EscrowStatus.HELD,
        verbose_name=_('Status')
    )
    
    # Timestamps
    held_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    # Release configuration
    auto_release_hours = models.IntegerField(
        default=24,
        verbose_name=_('Auto-release Hours'),
        help_text=_('Hours after checkout to auto-release funds')
    )
    
    class Meta:
        verbose_name = _('Escrow')
        verbose_name_plural = _('Escrows')
        ordering = ['-held_at']
        indexes = [
            models.Index(fields=['status', '-held_at']),
            models.Index(fields=['application']),
        ]
    
    def __str__(self):
        return f"Escrow {self.id} - {self.held_amount} ({self.status})"
    
    def release(self):
        """Mark escrow as released."""
        if self.status != EscrowStatus.HELD:
            raise ValueError(f"Cannot release escrow with status: {self.status}")
        
        self.status = EscrowStatus.RELEASED
        self.released_at = timezone.now()
        self.save(update_fields=['status', 'released_at'])
        
        return self
    
    def refund(self):
        """Mark escrow as refunded."""
        if self.status != EscrowStatus.HELD:
            raise ValueError(f"Cannot refund escrow with status: {self.status}")
        
        self.status = EscrowStatus.REFUNDED
        self.released_at = timezone.now()
        self.save(update_fields=['status', 'released_at'])
        
        return self


class Payout(models.Model):
    """
    Worker payout record.
    Created after escrow is released.
    Tracks transfer to worker's payment account.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='payouts',
        verbose_name=_('Transaction')
    )
    worker = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payouts',
        limit_choices_to={'user_type': 'worker'},
        verbose_name=_('Worker')
    )
    
    # Payout details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Payout Amount')
    )
    
    status = models.CharField(
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
        verbose_name=_('Status')
    )
    
    # PSP integration
    transfer_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Transfer ID'),
        help_text=_('PSP transfer identifier')
    )
    destination_account = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Destination Account'),
        help_text=_('Worker payment account ID')
    )
    
    # Error handling
    failure_reason = models.TextField(
        blank=True,
        verbose_name=_('Failure Reason')
    )
    retry_count = models.IntegerField(
        default=0,
        verbose_name=_('Retry Count')
    )
    
    # Timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Payout')
        verbose_name_plural = _('Payouts')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['status', '-initiated_at']),
            models.Index(fields=['worker', '-initiated_at']),
        ]
    
    def __str__(self):
        return f"Payout {self.id} - {self.amount} to {self.worker} ({self.status})"
    
    def mark_completed(self):
        """Mark payout as completed."""
        self.status = PayoutStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
        return self
    
    def mark_failed(self, reason):
        """Mark payout as failed with reason."""
        self.status = PayoutStatus.FAILED
        self.failed_at = timezone.now()
        self.failure_reason = reason
        self.retry_count += 1
        self.save(update_fields=['status', 'failed_at', 'failure_reason', 'retry_count'])
        return self
