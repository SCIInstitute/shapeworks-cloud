import os

from celery import Celery
import configurations.importer

from .manage_workers import manage_workers

os.environ['DJANGO_SETTINGS_MODULE'] = 'shapeworks_cloud.settings'
if not os.environ.get('DJANGO_CONFIGURATION'):
    raise ValueError('The environment variable "DJANGO_CONFIGURATION" must be set.')
configurations.importer.install()

# Using a string config_source means the worker doesn't have to serialize
# the configuration object to child processes.
app = Celery(config_source='django.conf:settings', namespace='CELERY')


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10, manage.s(), name='manage workers')
    sender.add_periodic_task(90, mock_task_reqs.s(), name='mock task requests')


@app.task
def manage():
    manage_workers()


@app.task
def mock_task_reqs():
    for index in range(5):
        id = app.send_task(
            'shapeworks_cloud.core.tasks.deepssm', kwargs={'index': index}, queue='gpu'
        )
        print(f'Task requested: {id}')


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
