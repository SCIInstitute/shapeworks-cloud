# import factory.django
# import factory.fuzzy

# from shapeworks_cloud.core import models


# class GroomedDatasetFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = models.GroomedDataset

#     name = factory.Faker('sentence')


# class GroomedSegmentationFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = models.GroomedSegmentation

#     name = factory.Faker('file_name', extension='nrrd')
#     blob = factory.django.FileField(data=b'fakeimagebytes', filename='fake.nrrd')
#     mesh = factory.django.FileField(data=b'fakemeshbytes', filename='fake.vtp')
#     dataset = factory.SubFactory(GroomedDatasetFactory)
#     index = factory.Sequence(lambda n: n)
