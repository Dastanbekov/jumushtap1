"""
Payment Service Provider (PSP) adapters.
Abstract interface for different payment providers.
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Tuple
import uuid

logger = logging.getLogger(__name__)


class PSPAdapter(ABC):
    """
    Abstract base class for PSP adapters.
    Implement this interface for different payment providers (Stripe, local, etc.).
    """
    
    @abstractmethod
    def create_payment_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment intent to hold funds.
        
        Returns:
            dict: {'intent_id': str, 'client_secret': str, 'status': str}
        """
        pass
    
    @abstractmethod
    def capture_payment(self, intent_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """
        Capture (charge) a held payment.
        
        Args:
            intent_id: Payment intent ID
            amount: Amount to capture (None = full amount)
        
        Returns:
            dict: {'success': bool, 'charge_id': str, 'status': str}
        """
        pass
    
    @abstractmethod
    def refund_payment(self, intent_id: str, reason: str = None) -> Dict[str, Any]:
        """
        Refund a payment.
        
        Returns:
            dict: {'success': bool, 'refund_id': str}
        """
        pass
    
    @abstractmethod
    def create_transfer(self, amount: Decimal, destination: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transfer funds to worker's account.
        
        Args:
            amount: Amount to transfer
            destination: Worker's payment account ID
            metadata: Additional data
        
        Returns:
            dict: {'success': bool, 'transfer_id': str, 'status': str}
        """
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify webhook signature and parse event.
        
        Returns:
            tuple: (is_valid: bool, event_data: dict)
        """
        pass


class MockPSPAdapter(PSPAdapter):
    """
    Mock PSP adapter for development/testing.
    Simulates payment operations without real money.
    """
    
    # Class-level storage to persist across instances
    _intents = {}
    _transfers = {}
    
    def __init__(self):
        pass  # Uses class-level storage
    
    def create_payment_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock payment intent."""
        intent_id = f"mock_pi_{uuid.uuid4().hex[:24]}"
        client_secret = f"mock_secret_{uuid.uuid4().hex[:32]}"
        
        MockPSPAdapter._intents[intent_id] = {
            'id': intent_id,
            'amount': float(amount),
            'currency': currency,
            'status': 'requires_capture',
            'metadata': metadata,
        }
        
        logger.info(f"[MOCK PSP] Created payment intent: {intent_id} for {amount} {currency}")
        
        return {
            'intent_id': intent_id,
            'client_secret': client_secret,
            'status': 'requires_capture',
        }
    
    def capture_payment(self, intent_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Capture mock payment."""
        if intent_id not in MockPSPAdapter._intents:
            return {'success': False, 'error': 'Intent not found'}
        
        intent = MockPSPAdapter._intents[intent_id]
        capture_amount = float(amount) if amount else intent['amount']
        
        logger.info(f"[MOCK PSP] Captured {capture_amount} from intent {intent_id}")
        
        intent['status'] = 'succeeded'
        intent['captured_amount'] = capture_amount
        
        return {
            'success': True,
            'charge_id': f"mock_ch_{uuid.uuid4().hex[:24]}",
            'status': 'succeeded',
        }
    
    def refund_payment(self, intent_id: str, reason: str = None) -> Dict[str, Any]:
        """Refund mock payment."""
        if intent_id not in MockPSPAdapter._intents:
            return {'success': False, 'error': 'Intent not found'}
        
        logger.info(f"[MOCK PSP] Refunded intent {intent_id}. Reason: {reason}")
        
        MockPSPAdapter._intents[intent_id]['status'] = 'refunded'
        
        return {
            'success': True,
            'refund_id': f"mock_re_{uuid.uuid4().hex[:24]}",
        }
    
    def create_transfer(self, amount: Decimal, destination: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock transfer."""
        transfer_id = f"mock_tr_{uuid.uuid4().hex[:24]}"
        
        MockPSPAdapter._transfers[transfer_id] = {
            'id': transfer_id,
            'amount': float(amount),
            'destination': destination,
            'status': 'paid',
            'metadata': metadata,
        }
        
        logger.info(f"[MOCK PSP] Transferred {amount} to {destination}")
        
        return {
            'success': True,
            'transfer_id': transfer_id,
            'status': 'paid',
        }
    
    def verify_webhook(self, payload: bytes, signature: str) -> Tuple[bool, Dict[str, Any]]:
        """Mock webhook verification (always valid in development)."""
        import json
        
        try:
            event_data = json.loads(payload)
            logger.info(f"[MOCK PSP] Webhook received: {event_data.get('type', 'unknown')}")
            return True, event_data
        except json.JSONDecodeError:
            return False, {}


class StripePSPAdapter(PSPAdapter):
    """
    Stripe PSP adapter.
    Real implementation for production use.
    """
    
    def __init__(self, api_key: str, webhook_secret: str):
        import stripe
        stripe.api_key = api_key
        self.stripe = stripe
        self.webhook_secret = webhook_secret
    
    def create_payment_intent(self, amount: Decimal, currency: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create Stripe payment intent."""
        intent = self.stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency.lower(),
            capture_method='manual',  # Hold funds
            metadata=metadata,
        )
        
        return {
            'intent_id': intent.id,
            'client_secret': intent.client_secret,
            'status': intent.status,
        }
    
    def capture_payment(self, intent_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Capture Stripe payment."""
        try:
            kwargs = {'payment_intent': intent_id}
            if amount:
                kwargs['amount_to_capture'] = int(amount * 100)
            
            intent = self.stripe.PaymentIntent.capture(**kwargs)
            
            return {
                'success': True,
                'charge_id': intent.latest_charge,
                'status': intent.status,
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe capture failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def refund_payment(self, intent_id: str, reason: str = None) -> Dict[str, Any]:
        """Refund Stripe payment."""
        try:
            refund = self.stripe.Refund.create(
                payment_intent=intent_id,
                reason='requested_by_customer' if not reason else reason,
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe refund failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_transfer(self, amount: Decimal, destination: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create Stripe transfer."""
        try:
            transfer = self.stripe.Transfer.create(
                amount=int(amount * 100),
                currency='usd',  # Or from settings
                destination=destination,
                metadata=metadata,
            )
            
            return {
                'success': True,
                'transfer_id': transfer.id,
                'status': transfer.status,
            }
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe transfer failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def verify_webhook(self, payload: bytes, signature: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify Stripe webhook signature."""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True, event
        except (ValueError, self.stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook verification failed: {e}")
            return False, {}


def get_psp_adapter() -> PSPAdapter:
    """
    Factory function to get configured PSP adapter.
    Reads from Django settings.
    """
    from django.conf import settings
    
    psp_provider = getattr(settings, 'PSP_PROVIDER', 'mock')
    
    if psp_provider == 'stripe':
        api_key = settings.STRIPE_SECRET_KEY
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        return StripePSPAdapter(api_key, webhook_secret)
    
    else:  # Default to mock
        return MockPSPAdapter()
