import os

from celery import Celery
from kombu import Queue
import configurations.importer

from .manage_workers import manage_workers

AWS_ENV_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']

os.environ['DJANGO_SETTINGS_MODULE'] = 'shapeworks_cloud.settings'
if not os.environ.get('DJANGO_CONFIGURATION'):
    raise ValueError('The environment variable "DJANGO_CONFIGURATION" must be set.')
configurations.importer.install()

# Using a string config_source means the worker doesn't have to serialize
# the configuration object to child processes.
app = Celery(
    config_source='django.conf:settings',
    namespace='CELERY',
    task_queues=(
    Queue('celery'), Queue('gpu', durable=False)
))

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Celery beat container should have these environment variables
    sender.add_periodic_task(
        20, manage.s(**{k: os.environ.get(k) for k in AWS_ENV_VARS}), name='manage workers'
    )


@app.task
def manage(**kwargs):
    manage_workers(**kwargs)


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
