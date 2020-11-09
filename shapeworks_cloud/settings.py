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


class ShapeworksCloudConfig(ConfigMixin):
    WSGI_APPLICATION = 'shapeworks_cloud.wsgi.application'
    ROOT_URLCONF = 'shapeworks_cloud.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        configuration.INSTALLED_APPS += [
            'shapeworks_cloud.core.apps.CoreConfig',
            's3_file_field',
        ]


class DevelopmentConfiguration(ShapeworksCloudConfig, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(ShapeworksCloudConfig, TestingBaseConfiguration):
    pass


class ProductionConfiguration(ShapeworksCloudConfig, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(ShapeworksCloudConfig, HerokuProductionBaseConfiguration):
    pass
