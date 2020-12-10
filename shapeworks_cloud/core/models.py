from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    # TimeStampedModel also provides "created" and "modified" fields


class BlobModel(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    blob = S3FileField()

    class Meta:
        abstract = True

    @property
    def formatted_size(self, base=1024, unit='B'):
        size = self.blob.size
        if size < base:
            return f'{size} {unit}'
        units = ['', 'K', 'M', 'G', 'T']
        i = 0
        while i < 5 and size >= base:
            size /= base
            i += 1
        return f'{size:.2f} {units[i]}{unit}'


class Segmentation(BlobModel):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='segmentations')


class Groomed(BlobModel):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='groomed')


class ShapeModel(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    analyze = S3FileField()
    correspondence = S3FileField()
    transform = S3FileField()
    magic_number = models.IntegerField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='shape_models')


class ShapeModelBlob(BlobModel):
    shape_model = models.ForeignKey(ShapeModel, on_delete=models.CASCADE, related_name='blobs')
