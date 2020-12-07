from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

ASSET_TYPE_CHOICES = [
    ('segmentation', 'Segmentation'),
    ('groomed', 'Groomed'),
    ('shape_model', 'Shape Model'),
]


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    # TimeStampedModel also provides "created" and "modified" fields


class Asset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    blob = S3FileField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='files')
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)

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
