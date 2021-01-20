import factory.django
import factory.fuzzy

from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('sentence')


class BlobFactory(factory.django.DjangoModelFactory):
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    subject = factory.Faker('random_int')


class GroomedFactory(BlobFactory):
    class Meta:
        model = Groomed

    dataset = factory.SubFactory(DatasetFactory)


class SegmentationFactory(BlobFactory):
    class Meta:
        model = Segmentation

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)


class ShapeModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShapeModel

    analyze = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    correspondence = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    transform = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    magic_number = factory.Faker('random_int')  # TODO powers of 2
    dataset = factory.SubFactory(DatasetFactory)


class ParticlesFactory(BlobFactory):
    class Meta:
        model = Particles

    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    shape_model = factory.SubFactory(ShapeModelFactory)
