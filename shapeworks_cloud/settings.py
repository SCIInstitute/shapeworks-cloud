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


class ShapeworksCloudMixin(ConfigMixin):
    WSGI_APPLICATION = 'shapeworks_cloud.wsgi.application'
    ROOT_URLCONF = 'shapeworks_cloud.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        configuration.INSTALLED_APPS += [
            'shapeworks_cloud.core.apps.CoreConfig',
            's3_file_field',
        ]
        configuration.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
            # Required for swagger logins
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ]


class DevelopmentConfiguration(ShapeworksCloudMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(ShapeworksCloudMixin, TestingBaseConfiguration):
    pass


class ProductionConfiguration(ShapeworksCloudMixin, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(ShapeworksCloudMixin, HerokuProductionBaseConfiguration):
    pass
