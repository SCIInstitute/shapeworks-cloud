import factory.django
import factory.fuzzy

from shapeworks_cloud.core import models


class GroomedDatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GroomedDataset

    name = factory.Faker('sentence')


class GroomedSegmentationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GroomedSegmentation

    name = factory.Faker('file_name', extension='nrrd')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.nrrd')
    mesh = factory.django.FileField(data=b'fakemeshbytes', filename='fake.vtp')
    dataset = factory.SubFactory(GroomedDatasetFactory)
    index = factory.Sequence(lambda n: n)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Project

    name = factory.Faker('sentence')
    groomed_dataset = factory.SubFactory(GroomedDatasetFactory)


# Eventually, we may want to include additional information on this object such as
# the number of particles, etc.
class ShapeModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ShapeModel

    blob = factory.django.FileField(data=b'fakeshapebytes', filename='fake.npy')


class OptimizationParametersFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OptimizationParameters

    optimization = factory.SubFactory(
        'shapeworks_cloud.core.tests.factories.OptimizationFactory', optimization=None
    )


class OptimizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Optimization

    project = factory.SubFactory(ProjectFactory)
    shape_model = factory.SubFactory(ShapeModelFactory)
    parameters = factory.RelatedFactory(
        OptimizationParametersFactory, factory_related_name='optimization'
    )


class OptimizationCheckpointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OptimizationCheckpoint

    split = factory.Faker('pyint')
    iteration = factory.Sequence(lambda n: n)
    optimization = factory.SubFactory(OptimizationFactory)
    shape_model = factory.SubFactory(ShapeModelFactory)
