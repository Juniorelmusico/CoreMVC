import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'melocuore.settings')

app = Celery('melocuore')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configure Celery to use Redis as message broker
app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Configure task settings
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.task_track_started = True
app.conf.task_time_limit = 3600  # 1 hour
app.conf.worker_prefetch_multiplier = 1 