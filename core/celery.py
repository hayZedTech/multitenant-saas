import os
from celery import Celery

# Set default Django settings module for celery command-line tool
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('multitenant_saas')

# Load task configuration keys directly from settings.py using 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover asynchronous tasks.py files inside all registered sub-apps
app.autodiscover_tasks()