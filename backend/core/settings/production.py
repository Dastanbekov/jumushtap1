"""
Production settings - inherits from base.
Enterprise-grade security and performance optimizations.
"""

from .base import *

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Security Headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# CORS - Strict whitelist
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# CSRF
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

# Database - Production optimizations
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 seconds
}

# Static files - Should be served via CDN/Nginx
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files - S3
USE_S3 = config('USE_S3', default=True, cast=bool)
if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Email - Production email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# SMS Provider
SMS_PROVIDER = config('SMS_PROVIDER', default='twilio')
if SMS_PROVIDER == 'twilio':
    TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER')

# Payment Provider
PSP_PROVIDER = config('PSP_PROVIDER', default='stripe')
if PSP_PROVIDER == 'stripe':
    STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET')

# Firebase Cloud Messaging
FCM_SERVER_KEY = config('FCM_SERVER_KEY')
FCM_CREDENTIALS_PATH = config('FCM_CREDENTIALS_PATH', default=None)

# Google Maps
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY')

# Logging - JSON structured logs for production
LOGGING['formatters']['default'] = LOGGING['formatters']['json']
LOGGING['handlers']['console']['formatter'] = 'json'
LOGGING['handlers']['file']['formatter'] = 'json'

# Admin site hardening
ADMIN_URL = config('ADMIN_URL', default='admin/')  # Should be obscure in production

# DRF - Production renderer
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]
