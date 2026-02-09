"""
Audit Log Middleware
Automatically logs critical actions (POST, PUT, DELETE, PATCH) for compliance and security.
"""

import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone

logger = logging.getLogger('apps.audit')


class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs all mutating requests (POST, PUT, PATCH, DELETE) with:
    - User ID
    - IP address
    - Correlation ID
    - Endpoint
    - Request body (sanitized)
    - Response status
    """
    
    MUTATING_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
    
    # Sensitive fields to exclude from logs
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'api_key', 
        'access_token', 'refresh_token', 'otp', 'code'
    }
    
    # Endpoints that should ALWAYS be logged
    CRITICAL_ENDPOINTS = {
        '/api/v1/auth/send-otp/',
        '/api/v1/auth/verify-otp/',
        '/api/v1/jobs/',
        '/api/v1/payments/',
        '/api/v1/check-in/',
    }
    
    def process_response(self, request, response):
        """
        Log after response to capture status code.
        """
        # Only log mutating methods or critical endpoints
        should_log = (
            request.method in self.MUTATING_METHODS or
            request.path in self.CRITICAL_ENDPOINTS
        )
        
        if not should_log:
            return response
        
        # Prepare log data
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user_id': self.get_user_id(request),
            'ip_address': self.get_client_ip(request),
            'correlation_id': getattr(request, 'correlation_id', None),
            'status_code': response.status_code,
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }
        
        # Add sanitized request body for POST/PUT/PATCH
        if request.method in {'POST', 'PUT', 'PATCH'}:
            log_data['request_body'] = self.sanitize_data(
                self.get_request_body(request)
            )
        
        # Log with appropriate level
        if 200 <= response.status_code < 400:
            logger.info('Audit log', extra=log_data)
        else:
            logger.warning('Audit log - Error', extra=log_data)
        
        return response
    
    def get_user_id(self, request):
        """Extract user ID if authenticated."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None
    
    @staticmethod
    def get_client_ip(request):
        """Get real client IP."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def get_request_body(request):
        """Safely parse request body."""
        try:
            if hasattr(request, 'data'):
                return request.data
            if request.body:
                return json.loads(request.body.decode('utf-8'))
        except (ValueError, AttributeError):
            pass
        return {}
    
    def sanitize_data(self, data):
        """
        Remove sensitive fields from data before logging.
        Protects PII and secrets.
        """
        if not isinstance(data, dict):
            return '[non-dict data]'
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_FIELDS:
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Truncate long strings
                if isinstance(value, str) and len(value) > 200:
                    sanitized[key] = value[:200] + '...'
                else:
                    sanitized[key] = value
        
        return sanitized
