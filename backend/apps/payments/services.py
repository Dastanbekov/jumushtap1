"""
Services for Payment system.
Business logic for escrow, transactions, and payouts.
"""

import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import Transaction, Escrow, Payout, TransactionStatus, EscrowStatus, PayoutStatus
from .psp_adapter import get_psp_adapter
from apps.jobs.models import JobApplication, CheckIn

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for managing payments, escrow, and payouts.
    """
    
    PLATFORM_FEE_PERCENTAGE = Decimal('0.10')  # 10% commission
    
    @classmethod
    @transaction.atomic
    def create_escrow_for_application(cls, application: JobApplication):
        """
        Create escrow when business accepts worker application.
        Holds funds until job completion.
        
        Args:
            application:JobApplication (must be accepted)
        
        Returns:
            tuple: (Transaction, Escrow)
        """
        job = application.job
        
        # Calculate amount
        estimated_amount = job.hourly_rate * Decimal(str(job.duration_hours))
        
        # Generate idempotency key
        idempotency_key = f"escrow_create_{application.id}"
        
        # Check if transaction already exists
        existing = Transaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            logger.info(f"Transaction already exists for application {application.id}")
            return existing, existing.escrow
        
        # Create PSP payment intent
        psp = get_psp_adapter()
        
        try:
            intent_result = psp.create_payment_intent(
                amount=estimated_amount,
                currency='KGS',  # Or from settings
                metadata={
                    'job_id': str(job.id),
                    'application_id': str(application.id),
                    'business_id': str(job.business.id),
                    'worker_id': str(application.worker.id),
                }
            )
            
            # Create transaction record
            trans = Transaction.objects.create(
                job=job,
                business=job.business,
                worker=application.worker,
                amount=estimated_amount,
                status=TransactionStatus.PENDING,
                payment_intent_id=intent_result['intent_id'],
                idempotency_key=idempotency_key,
                metadata={
                    'client_secret': intent_result.get('client_secret'),
                    'estimated': True,
                }
            )
            
            # Calculate fees
            trans.calculate_fees(cls.PLATFORM_FEE_PERCENTAGE)
            trans.save()
            
            # Create escrow
            escrow = Escrow.objects.create(
                transaction=trans,
                application=application,
                held_amount=estimated_amount,
                status=EscrowStatus.HELD
            )
            
            logger.info(
                f"Escrow created: {escrow.id} for application {application.id}. "
                f"Amount: {estimated_amount}"
            )
            
            return trans, escrow
        
        except Exception as e:
            logger.error(f"Failed to create escrow for application {application.id}: {e}", exc_info=True)
            raise
    
    @classmethod
    @transaction.atomic
    def release_escrow_after_checkout(cls, checkin: CheckIn):
        """
        Release escrow after worker checks out.
        Calculates actual payment based on worked hours.
        
        Args:
            checkin: CheckIn instance (must be checked out)
        
        Returns:
            Payout instance
        """
        if not checkin.is_checked_out:
            raise ValueError("Cannot release escrow: worker not checked out")
        
        application = checkin.application
        
        try:
            escrow = Escrow.objects.get(application=application)
        except Escrow.DoesNotExist:
            raise ValueError(f"No escrow found for application {application.id}")
        
        if escrow.status != EscrowStatus.HELD:
            raise ValueError(f"Escrow already {escrow.status}")
        
        trans = escrow.transaction
        
        # Calculate actual payment
        worked_hours = Decimal(str(checkin.worked_hours))
        hourly_rate = application.job.hourly_rate
        actual_amount = worked_hours * hourly_rate
        
        # Update transaction with actual amounts
        trans.amount = actual_amount
        trans.calculate_fees(cls.PLATFORM_FEE_PERCENTAGE)
        trans.save()
        
        # Capture payment via PSP
        psp = get_psp_adapter()
        
        try:
            capture_result = psp.capture_payment(
                intent_id=trans.payment_intent_id,
                amount=actual_amount
            )
            
            if not capture_result.get('success', True):  # Mock PSP doesn't return 'success'
                raise Exception(f"PSP capture failed: {capture_result.get('error')}")
            
            # Update transaction status
            trans.status = TransactionStatus.HELD
            trans.save()
            
            # Create payout to worker
            payout = cls._create_payout(trans, application.worker, trans.worker_payout)
            
            # Release escrow
            escrow.release()
            
            logger.info(
                f"Escrow released for application {application.id}. "
                f"Worked: {worked_hours}h, Amount: {actual_amount}"
            )
            
            return payout
        
        except Exception as e:
            logger.error(f"Failed to release escrow for application {application.id}: {e}", exc_info=True)
            # Don't mark as failed, might be retryable
            raise
    
    @classmethod
    @transaction.atomic
    def _create_payout(cls, trans: Transaction, worker, amount: Decimal):
        """
        Create payout to worker.
        Initiates transfer via PSP.
        """
        # Get worker's payment account
        try:
            payment_account = worker.worker_profile.payment_account_id
        except AttributeError:
            payment_account = None
        
        if not payment_account:
            logger.warning(f"Worker {worker.id} has no payment account configured")
            payment_account = 'mock_account'  # For development
        
        # Create payout record
        payout = Payout.objects.create(
            transaction=trans,
            worker=worker,
            amount=amount,
            destination_account=payment_account,
            status=PayoutStatus.PENDING
        )
        
        # Initiate transfer via PSP
        psp = get_psp_adapter()
        
        try:
            transfer_result = psp.create_transfer(
                amount=amount,
                destination=payment_account,
                metadata={
                    'payout_id': str(payout.id),
                    'transaction_id': str(trans.id),
                    'worker_id': str(worker.id),
                }
            )
            
            if transfer_result.get('success', True):
                payout.transfer_id = transfer_result['transfer_id']
                payout.status = PayoutStatus.PROCESSING
                payout.save()
                
                logger.info(f"Payout initiated: {payout.id} for {amount}")
                
                # Notify worker
                from apps.notifications.services import NotificationService
                try:
                    NotificationService.notify_payment_released(payout)
                except Exception as e:
                    logger.error(f"Failed to notify worker about payout {payout.id}: {e}")
                    
            else:
                payout.mark_failed(f"Transfer failed: {transfer_result.get('error')}")
        
        except Exception as e:
            logger.error(f"Failed to create payout {payout.id}: {e}", exc_info=True)
            payout.mark_failed(str(e))
        
        return payout
    
    @classmethod
    @transaction.atomic
    def refund_escrow(cls, trans: Transaction, reason: str = None):
        """
        Refund escrow to business.
        Used when job is cancelled before completion.
        
        Args:
            trans: Transaction instance
            reason: Refund reason
        
        Returns:
            Transaction instance
        """
        if trans.status not in [TransactionStatus.PENDING, TransactionStatus.HELD]:
            raise ValueError(f"Cannot refund transaction with status: {trans.status}")
        
        try:
            escrow = trans.escrow
        except Escrow.DoesNotExist:
            raise ValueError(f"No escrow found for transaction {trans.id}")
        
        if escrow.status != EscrowStatus.HELD:
            raise ValueError(f"Escrow already {escrow.status}")
        
        # Refund via PSP
        psp = get_psp_adapter()
        
        try:
            refund_result = psp.refund_payment(
                intent_id=trans.payment_intent_id,
                reason=reason
            )
            
            if not refund_result.get('success', True):
                raise Exception(f"PSP refund failed: {refund_result.get('error')}")
            
            # Update transaction
            trans.status = TransactionStatus.REFUNDED
            trans.metadata['refund_reason'] = reason
            trans.metadata['refund_id'] = refund_result.get('refund_id')
            trans.save()
            
            # Update escrow
            escrow.refund()
            
            logger.info(f"Escrow refunded: {escrow.id}. Reason: {reason}")
            
            return trans
        
        except Exception as e:
            logger.error(f"Failed to refund escrow {escrow.id}: {e}", exc_info=True)
            trans.status = TransactionStatus.FAILED
            trans.metadata['failure_reason'] = str(e)
            trans.save()
            raise
    
    @classmethod
    @transaction.atomic
    def complete_payout(cls, payout_id: str):
        """
        Mark payout as completed.
        Called from webhook when transfer succeeds.
        """
        try:
            payout = Payout.objects.get(id=payout_id)
        except Payout.DoesNotExist:
            logger.error(f"Payout not found: {payout_id}")
            return None
        
        if payout.status == PayoutStatus.COMPLETED:
            logger.info(f"Payout {payout_id} already completed")
            return payout
        
        payout.mark_completed()
        
        # Mark transaction as completed
        trans = payout.transaction
        trans.status = TransactionStatus.COMPLETED
        trans.completed_at = timezone.now()
        trans.save()
        
        logger.info(f"Payout completed: {payout.id}")
        
        return payout


class WebhookService:
    """
    Service for handling PSP webhooks.
    """
    
    @staticmethod
    def handle_webhook(payload: bytes, signature: str):
        """
        Handle incoming webhook from PSP.
        Verifies signature and processes event.
        
        Args:
            payload: Raw request body
            signature: Webhook signature header
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        psp = get_psp_adapter()
        
        # Verify webhook
        is_valid, event_data = psp.verify_webhook(payload, signature)
        
        if not is_valid:
            logger.error("Invalid webhook signature")
            return {'success': False, 'message': 'Invalid signature'}
        
        event_type = event_data.get('type', 'unknown')
        
        logger.info(f"Processing webhook: {event_type}")
        
        # Route to appropriate handler
        handlers = {
            'payment_intent.succeeded': WebhookService._handle_payment_succeeded,
            'payment_intent.payment_failed': WebhookService._handle_payment_failed,
            'transfer.paid': WebhookService._handle_transfer_paid,
            'transfer.failed': WebhookService._handle_transfer_failed,
        }
        
        handler = handlers.get(event_type)
        
        if handler:
            try:
                handler(event_data.get('data', {}).get('object', {}))
                return {'success': True, 'message': f'Processed {event_type}'}
            except Exception as e:
                logger.error(f"Webhook handler failed for {event_type}: {e}", exc_info=True)
                return {'success': False, 'message': str(e)}
        else:
            logger.warning(f"No handler for webhook type: {event_type}")
            return {'success': True, 'message': 'Ignored'}
    
    @staticmethod
    @transaction.atomic
    def _handle_payment_succeeded(intent_data: dict):
        """Handle successful payment intent."""
        intent_id = intent_data.get('id')
        
        try:
            trans = Transaction.objects.get(payment_intent_id=intent_id)
            if trans.status == TransactionStatus.PENDING:
                trans.status = TransactionStatus.HELD
                trans.save()
                logger.info(f"Transaction {trans.id} marked as held")
        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for intent: {intent_id}")
    
    @staticmethod
    @transaction.atomic
    def _handle_payment_failed(intent_data: dict):
        """Handle failed payment intent."""
        intent_id = intent_data.get('id')
        
        try:
            trans = Transaction.objects.get(payment_intent_id=intent_id)
            trans.status = TransactionStatus.FAILED
            trans.metadata['failure_reason'] = intent_data.get('last_payment_error', {}).get('message')
            trans.save()
            logger.error(f"Transaction {trans.id} failed")
        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for intent: {intent_id}")
    
    @staticmethod
    @transaction.atomic
    def _handle_transfer_paid(transfer_data: dict):
        """Handle successful transfer (payout)."""
        transfer_id = transfer_data.get('id')
        
        try:
            payout = Payout.objects.get(transfer_id=transfer_id)
            PaymentService.complete_payout(str(payout.id))
        except Payout.DoesNotExist:
            logger.error(f"Payout not found for transfer: {transfer_id}")
    
    @staticmethod
    @transaction.atomic
    def _handle_transfer_failed(transfer_data: dict):
        """Handle failed transfer."""
        transfer_id = transfer_data.get('id')
        
        try:
            payout = Payout.objects.get(transfer_id=transfer_id)
            failure_reason = transfer_data.get('failure_message', 'Unknown error')
            payout.mark_failed(failure_reason)
            logger.error(f"Payout {payout.id} failed: {failure_reason}")
        except Payout.DoesNotExist:
            logger.error(f"Payout not found for transfer: {transfer_id}")
