import logging
import firebase_admin
from firebase_admin import messaging, credentials
import os

logger = logging.getLogger(__name__)

# Initialize Firebase
# Ensure GOOGLE_APPLICATION_CREDENTIALS env var is set or use mock for dev
if not firebase_admin._apps:
    try:
        # Check if credential file exists, otherwise warn
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin initialized with credentials")
        else:
            # Initialize with default strategies (e.g. metadata service)
            # or mock/no-op if dev
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not found. Firebase initialized in default mode (might fail without auth).")
            firebase_admin.initialize_app() 
    except Exception as e:
        logger.warning(f"Firebase Init Failed: {e}")


class NotificationService:
    @staticmethod
    def send_push(user, title, body, data=None):
        """
        Send FCM push notification to a user.
        """
        if not user.fcm_token:
            logger.debug(f"User {user.id} has no FCM token")
            return None
        
        # In a real app, you might check 'notification_settings' here based on category
        # e.g. if category == 'promo' and not user.notification_settings.promo: return

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=user.fcm_token,
        )

        try:
            response = messaging.send(message)
            logger.info(f"Successfully sent message to {user.id}: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending message to {user.id}: {e}")
            return None

    @staticmethod
    def send_to_topic(topic, title, body, data=None):
        # Implementation for geo-topics if needed
        pass
