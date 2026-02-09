"""
Services for Notifications app.
"""

import logging
from typing import Dict, Any
from django.db import transaction

from .models import Device, Notification
from .fcm import get_fcm_adapter

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications.
    """
    
    @staticmethod
    def register_device(user, token: str, device_type: str = 'android'):
        """
        Register a device for push notifications.
        Updates existing device if token already exists.
        """
        device, created = Device.objects.update_or_create(
            registration_id=token,
            defaults={
                'user': user,
                'device_type': device_type,
                'active': True
            }
        )
        return device
    
    @staticmethod
    def send_notification(user, title: str, body: str, data: Dict[str, Any] = None):
        """
        Send notification to a user's active devices.
        Also creates a history record.
        """
        # Create history record
        Notification.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {}
        )
        
        # Get active devices
        devices = Device.objects.filter(user=user, active=True)
        tokens = list(devices.values_list('registration_id', flat=True))
        
        if not tokens:
            logger.info(f"No active devices for user {user.id}")
            return 0
        
        # Send via FCM
        adapter = get_fcm_adapter()
        success_count = adapter.send_multicast(tokens, title, body, data)
        
        logger.info(f"Sent notification to user {user.id}: {title} (Success: {success_count}/{len(tokens)})")
        return success_count
    
    # --- Preset Notifications ---
    
    @classmethod
    def notify_application_received(cls, job, application):
        """Notify business about new application."""
        cls.send_notification(
            user=job.business,
            title="New Application Received",
            body=f"{application.worker.worker_profile.full_name} applied to {job.title}",
            data={
                'type': 'application_received',
                'job_id': str(job.id),
                'application_id': str(application.id)
            }
        )
    
    @classmethod
    def notify_application_accepted(cls, application):
        """Notify worker that application was accepted."""
        cls.send_notification(
            user=application.worker,
            title="Application Accepted! 🎉",
            body=f"You have been accepted for: {application.job.title}",
            data={
                'type': 'application_accepted',
                'job_id': str(application.job.id),
                'application_id': str(application.id)
            }
        )
    
    @classmethod
    def notify_application_rejected(cls, application):
        """Notify worker that application was rejected."""
        cls.send_notification(
            user=application.worker,
            title="Application Update",
            body=f"Status update for: {application.job.title}",
            data={
                'type': 'application_rejected',
                'job_id': str(application.job.id),
                'application_id': str(application.id)
            }
        )
    
    @classmethod
    def notify_job_started(cls, job):
        """Notify business/worker that job started."""
        # This might be redundant if check-in notification is sent
        pass
    
    @classmethod
    def notify_worker_checked_in(cls, checkin):
        """Notify business that worker checked in."""
        worker_name = checkin.application.worker.worker_profile.full_name
        cls.send_notification(
            user=checkin.application.job.business,
            title="Worker Checked In ✅",
            body=f"{worker_name} checked in at {checkin.checked_in_at.strftime('%H:%M')}",
            data={
                'type': 'worker_checkin',
                'job_id': str(checkin.application.job.id),
                'checkin_id': str(checkin.id)
            }
        )
    
    @classmethod
    def notify_worker_checked_out(cls, checkin):
        """Notify business that worker checked out."""
        worker_name = checkin.application.worker.worker_profile.full_name
        cls.send_notification(
            user=checkin.application.job.business,
            title="Worker Checked Out 🏁",
            body=f"{worker_name} checked out. Worked: {checkin.worked_hours:.1f}h",
            data={
                'type': 'worker_checkout',
                'job_id': str(checkin.application.job.id),
                'checkin_id': str(checkin.id)
            }
        )
    
    @classmethod
    def notify_payment_released(cls, payout):
        """Notify worker about payment."""
        cls.send_notification(
            user=payout.worker,
            title="Payment Released! 💰",
            body=f"You received {payout.amount} KGS for {payout.transaction.job.title}",
            data={
                'type': 'payment_released',
                'payout_id': str(payout.id),
                'amount': str(payout.amount)
            }
        )
