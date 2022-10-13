from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'shapeworks_cloud.core'
    verbose_name = 'ShapeWorks Cloud: Core'

    def ready(self):
        import shapeworks_cloud.core.signals  # NOQA
