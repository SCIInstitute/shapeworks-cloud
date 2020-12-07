import factory.django
import factory.fuzzy

from shapeworks_cloud.core.models import ASSET_TYPE_CHOICES, Asset, Dataset


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = factory.Faker('sentence')


class AssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Asset

    name = factory.Faker('file_name', category='image')
    blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.png')
    dataset = factory.SubFactory(DatasetFactory)
    asset_type = factory.fuzzy.FuzzyChoice([c[0] for c in ASSET_TYPE_CHOICES])
