release: ./manage.py migrate
web: gunicorn --bind 0.0.0.0:$PORT shapeworks_cloud.wsgi
beat: celery --app shapeworks_cloud.celery beat
