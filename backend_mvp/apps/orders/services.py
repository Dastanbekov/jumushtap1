import math
import logging
from django.contrib.auth import get_user_model
from apps.notifications.services import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()

class MatchingService:
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        if not all([lat1, lon1, lat2, lon2]):
            return float('inf')
        
        try:
            lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        except ValueError:
            return float('inf')

        R = 6371  # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @staticmethod
    def notify_nearby_workers(order, radius_km=5):
        """
        Finds workers within radius_km of the order and sends push notification.
        """
        if not order.latitude or not order.longitude:
            logger.warning(f"Order {order.id} has no location, skipping matching.")
            return

        # 1. Get all workers (Optimization: Filter by city/region if available)
        # For MVP, we iterate. In Production, use PostGIS 'dwithin'.
        workers = User.objects.filter(role='worker', status='active').select_related('worker_profile', 'notification_settings')
        
        count = 0
        for worker in workers:
            try:
                profile = worker.worker_profile
                settings = getattr(worker, 'notification_settings', None)
                
                # Check Settings
                if settings and not settings.new_shift_nearby:
                    continue

                # Check Distance
                dist = MatchingService.calculate_distance(
                    order.latitude, order.longitude,
                    profile.last_latitude, profile.last_longitude
                )
                
                if dist <= radius_km:
                    # Match found! Send Push using NotificationService
                    title = "New Shift Nearby! 📍"
                    body = f"New job '{order.title}' is available {dist:.1f}km away."
                    data = {
                        "type": "new_order",
                        "order_id": str(order.id),
                        "distance": str(dist)
                    }
                    NotificationService.send_push(worker, title, body, data)
                    count += 1
            except Exception as e:
                logger.error(f"Error checking worker {worker.id}: {e}")
                continue
        
        logger.info(f"Notified {count} workers for Order {order.id}")
