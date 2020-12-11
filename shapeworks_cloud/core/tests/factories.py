import factory.django
import factory.fuzzy

from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('sentence')


class GroomedFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Groomed

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)


class SegmentationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Segmentation

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)


class ShapeModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShapeModel

    name = factory.Faker('file_name', category='image')
    analyze = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    correspondence = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    transform = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    magic_number = factory.Faker('int')  # TODO powers of 2
    dataset = factory.SubFactory(DatasetFactory)


class ParticlesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Particles

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    shape_model = factory.SubFactory(ShapeModelFactory)
