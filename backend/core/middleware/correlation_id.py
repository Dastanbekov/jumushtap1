"""
Correlation ID Middleware
Adds unique correlation ID to every request for distributed tracing and audit logs.
"""

import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIDMiddleware(MiddlewareMixin):
    """
    Adds X-Correlation-ID to every request and response.
    If client provides one, use it; otherwise generate new UUID.
    """
    
    HEADER_NAME = 'HTTP_X_CORRELATION_ID'
    RESPONSE_HEADER = 'X-Correlation-ID'
    
    def process_request(self, request):
        """
        Extract or generate correlation ID and attach to request.
        """
        correlation_id = request.META.get(self.HEADER_NAME)
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Attach to request for use in views/services
        request.correlation_id = correlation_id
        
        # Add to logging context (requires structlog or custom filter)
        logger.info(
            f"Request started",
            extra={
                'correlation_id': correlation_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': self.get_client_ip(request),
            }
        )
        
        return None
    
    def process_response(self, request, response):
        """
        Add correlation ID to response headers.
        """
        if hasattr(request, 'correlation_id'):
            response[self.RESPONSE_HEADER] = request.correlation_id
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """
        Get real client IP (handles proxies/load balancers).
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
