"""
Celery configuration for JumushTap
Async task processing for notifications, reports, etc.
"""

import os
from celery import Celery
from decouple import config

# Set Django settings module
env = config('DJANGO_ENV', default='development')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'core.settings.{env}')

app = Celery('jumushtap')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')
