"""
Custom exception handler for DRF
Provides consistent error responses and logging.
"""

import logging
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides:
    - Consistent error response format
    - Correlation ID in errors
    - Automatic error logging
    
    Format:
    {
        "error": "Error type",
        "detail": "Human-readable message",
        "correlation_id": "uuid",
        "field_errors": {...}  # For validation errors
    }
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)
    
    # Get request from context
    request = context.get('request')
    correlation_id = getattr(request, 'correlation_id', None) if request else None
    
    if response is not None:
        # Customize response format
        custom_response_data = {
            'error': exc.__class__.__name__,
            'detail': str(exc),
        }
        
        # Add correlation ID if available
        if correlation_id:
            custom_response_data['correlation_id'] = correlation_id
        
        # Handle validation errors (400)
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            custom_response_data['field_errors'] = exc.detail
        
        response.data = custom_response_data
        
        # Log error
        if response.status_code >= 500:
            logger.error(
                f"Server error: {exc}",
                extra={
                    'correlation_id': correlation_id,
                    'exception_type': exc.__class__.__name__,
                    'status_code': response.status_code,
                    'path': request.path if request else None,
                },
                exc_info=True,
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Client error: {exc}",
                extra={
                    'correlation_id': correlation_id,
                    'exception_type': exc.__class__.__name__,
                    'status_code': response.status_code,
                    'path': request.path if request else None,
                },
            )
    else:
        # Handle non-DRF exceptions
        logger.error(
            f"Unhandled exception: {exc}",
            extra={'correlation_id': correlation_id},
            exc_info=True,
        )
        
        response = Response(
            {
                'error': 'InternalServerError',
                'detail': 'An unexpected error occurred. Please try again later.',
                'correlation_id': correlation_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    return response
