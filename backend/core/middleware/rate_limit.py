"""
Rate Limiting Middleware
Redis-based rate limiting to prevent abuse and DoS attacks.
Enterprise-grade with per-user, per-IP, and per-endpoint limits.
"""

import logging
import time
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Flexible rate limiting middleware using Redis.
    
    Limits can be configured per:
    - Endpoint (e.g., OTP endpoints)
    - User (authenticated)
    - IP address (anonymous)
    """
    
    # Endpoint-specific rate limits (requests per minute)
    ENDPOINT_LIMITS = {
        '/api/v1/auth/send-otp/': 5,  # Max 5 OTP requests per minute
        '/api/v1/auth/verify-otp/': 10,
        '/api/v1/auth/login/': 5,
        '/api/v1/jobs/apply/': 10,  # Prevent spam applications
        '/api/v1/check-in/': 10,
    }
    
    # Default limits
    DEFAULT_USER_LIMIT = 60  # 60 requests per minute for authenticated users
    DEFAULT_ANON_LIMIT = 20  # 20 requests per minute for anonymous
    
    def process_request(self, request):
        """
        Check rate limits before processing request.
        """
        # Skip if rate limiting is disabled
        if not getattr(settings, 'RATE_LIMIT_ENABLE', True):
            return None
        
        # Get limit for this endpoint/user
        limit, window = self.get_limit(request)
        
        # Generate cache key
        cache_key = self.get_cache_key(request)
        
        # Check current count
        current = cache.get(cache_key, 0)
        
        # Log excessive requests
        if current >= limit:
            logger.warning(
                f"Rate limit exceeded",
                extra={
                    'cache_key': cache_key,
                    'current': current,
                    'limit': limit,
                    'path': request.path,
                    'user_id': self.get_user_id(request),
                    'ip': self.get_client_ip(request),
                    'correlation_id': getattr(request, 'correlation_id', None),
                }
            )
            
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'detail': f'Too many requests. Please try again in {window} seconds.',
                'retry_after': window,
            }, status=429)
        
        # Increment counter
        if current == 0:
            # First request in window - set with expiry
            cache.set(cache_key, 1, window)
        else:
            # Increment existing counter
            cache.incr(cache_key)
        
        # Add rate limit headers to response
        request.rate_limit_current = current + 1
        request.rate_limit_limit = limit
        
        return None
    
    def process_response(self, request, response):
        """
        Add rate limit headers to response.
        """
        if hasattr(request, 'rate_limit_limit'):
            response['X-RateLimit-Limit'] = str(request.rate_limit_limit)
            response['X-RateLimit-Remaining'] = str(
                max(0, request.rate_limit_limit - request.rate_limit_current)
            )
        
        return response
    
    def get_limit(self, request):
        """
        Determine rate limit for this request.
        Returns (limit, window_seconds).
        """
        # Check endpoint-specific limits first
        for endpoint, limit_per_min in self.ENDPOINT_LIMITS.items():
            if request.path.startswith(endpoint):
                return limit_per_min, 60
        
        # Default limits
        if hasattr(request, 'user') and request.user.is_authenticated:
            return self.DEFAULT_USER_LIMIT, 60
        else:
            return self.DEFAULT_ANON_LIMIT, 60
    
    def get_cache_key(self, request):
        """
        Generate unique cache key for rate limiting.
        Format: ratelimit:{endpoint}:{user_id|ip}
        """
        # Use endpoint as part of key
        endpoint_hash = request.path.replace('/', ':')
        
        # Use user ID if authenticated, otherwise IP
        if hasattr(request, 'user') and request.user.is_authenticated:
            identifier = f'user:{request.user.id}'
        else:
            identifier = f'ip:{self.get_client_ip(request)}'
        
        return f'ratelimit{endpoint_hash}:{identifier}'
    
    @staticmethod
    def get_client_ip(request):
        """Get real client IP."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    @staticmethod
    def get_user_id(request):
        """Get user ID if authenticated."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None
