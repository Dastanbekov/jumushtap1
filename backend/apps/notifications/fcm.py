"""
FCM Adapter for Push Notifications.
Handles interaction with Firebase Cloud Messaging.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FCMAdapter(ABC):
    """
    Abstract base class for FCM adapters.
    """
    
    @abstractmethod
    def send_multicast(self, tokens: List[str], title: str, body: str, data: Dict[str, Any] = None) -> int:
        """
        Send notification to multiple devices.
        
        Args:
            tokens: List of FCM registration tokens
            title: Notification title
            body: Notification body
            data: Custom data dictionary
        
        Returns:
            int: Number of successful messages
        """
        pass


class MockFCMAdapter(FCMAdapter):
    """
    Mock FCM adapter for development.
    Logs notifications to console.
    """
    
    def send_multicast(self, tokens: List[str], title: str, body: str, data: Dict[str, Any] = None) -> int:
        """Log notification to console."""
        if not tokens:
            return 0
            
        logger.info(f"[MOCK FCM] Sending to {len(tokens)} devices")
        logger.info(f"[MOCK FCM] Title: {title}")
        logger.info(f"[MOCK FCM] Body: {body}")
        if data:
            logger.info(f"[MOCK FCM] Data: {data}")
            
        return len(tokens)


class FirebaseFCMAdapter(FCMAdapter):
    """
    Real Firebase CLoud Messaging adapter.
    Uses firebase-admin SDK.
    """
    
    def __init__(self):
        import firebase_admin
        from firebase_admin import messaging, credentials
        from django.conf import settings
        
        # Initialize app if not already initialized
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                raise
        
        self.messaging = messaging
    
    def send_multicast(self, tokens: List[str], title: str, body: str, data: Dict[str, Any] = None) -> int:
        """Send via Firebase."""
        if not tokens:
            return 0
        
        # Helper to convert all data values to strings (FCM requirement)
        str_data = {k: str(v) for k, v in data.items()} if data else {}
        
        message = self.messaging.MulticastMessage(
            notification=self.messaging.Notification(
                title=title,
                body=body,
            ),
            data=str_data,
            tokens=tokens,
        )
        
        try:
            response = self.messaging.send_multicast(message)
            
            if response.failure_count > 0:
                responses = response.responses
                failed_tokens = []
                for idx, resp in enumerate(responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
                
                logger.warning(f"FCM: {response.failure_count} messages failed")
                # TODO: Handle invalid tokens (cleanup)
                
            return response.success_count
            
        except Exception as e:
            logger.error(f"FCM send failed: {e}")
            return 0


def get_fcm_adapter() -> FCMAdapter:
    """
    Factory function to get FCM adapter.
    """
    from django.conf import settings
    
    # Check if Firebase is configured
    use_firebase = getattr(settings, 'USE_FIREBASE', False)
    
    if use_firebase:
        try:
            return FirebaseFCMAdapter()
        except Exception:
            logger.warning("Components for Firebase missing, falling back to Mock")
            return MockFCMAdapter()
    else:
        return MockFCMAdapter()
