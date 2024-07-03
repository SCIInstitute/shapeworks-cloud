from __future__ import annotations

from pathlib import Path

from composed_configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    TestingBaseConfiguration,
)
from configurations import values


class ShapeworksCloudMixin(ConfigMixin):
    WSGI_APPLICATION = 'shapeworks_cloud.wsgi.application'
    ROOT_URLCONF = 'shapeworks_cloud.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    API_URL = values.URLValue(environ_required=True)

    HOMEPAGE_REDIRECT_URL = values.URLValue(environ_required=True)

    # This is required for the /api/v1/logout/ view to have access to the session cookie.
    CORS_ALLOW_CREDENTIALS = True

    CELERY_BROKER_POOL_LIMIT = 10

    DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        # Install local apps first, to ensure any overridden resources are found first
        configuration.INSTALLED_APPS = [
            'shapeworks_cloud.core.apps.CoreConfig',
        ] + configuration.INSTALLED_APPS

        # Install additional apps
        configuration.INSTALLED_APPS += [
            's3_file_field',
        ]

        configuration.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
            'rest_framework.authentication.TokenAuthentication',
        ]
        configuration.REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'] = [
            'django_filters.rest_framework.DjangoFilterBackend',
        ]


class DevelopmentConfiguration(ShapeworksCloudMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(ShapeworksCloudMixin, TestingBaseConfiguration):
    pass


class ProductionConfiguration(ShapeworksCloudMixin, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(ShapeworksCloudMixin, HerokuProductionBaseConfiguration):
    ALLOWED_HOSTS = ['shapeworks-cloud.herokuapp.com', 'herokuapp.com', 'app.shapeworks-cloud.org']
    LOGIN_REDIRECT_URL = 'https://www.shapeworks-cloud.org'
