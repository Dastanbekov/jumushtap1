"""
Development settings - for local development ONLY.
Inherits from base.py and overrides with development-specific configurations.
"""

from .base import *  # noqa
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts for development
ALLOWED_HOSTS = ['*']

# Use SQLite for development instead of PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend: console output (no actual emails sent)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging: more verbose for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Disable password validation for easier testing
AUTH_PASSWORD_VALIDATORS = []

# Static files
STATICFILES_DIRS = []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CORS: allow all origins for development
CORS_ALLOW_ALL_ORIGINS = True
