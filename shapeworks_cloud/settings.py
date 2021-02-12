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


class DevelopmentConfiguration(ShapeworksCloudMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(ShapeworksCloudMixin, TestingBaseConfiguration):
    pass


class ProductionConfiguration(ShapeworksCloudMixin, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(ShapeworksCloudMixin, HerokuProductionBaseConfiguration):
    pass
