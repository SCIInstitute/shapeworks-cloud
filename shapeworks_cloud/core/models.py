from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .metadata import METADATA_FIELDS, generate_filename


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    groomed_pattern = models.CharField(max_length=255, null=False, blank=True, default='')
    segmentation_pattern = models.CharField(max_length=255, null=False, blank=True, default='')
    particles_pattern = models.CharField(max_length=255, null=False, blank=True, default='')


class BlobModel(TimeStampedModel, models.Model):
    blob = S3FileField()

    # Each member of METADATA_FIELDS has a corresponding field here
    subject = models.IntegerField(null=False)

    class Meta:
        abstract = True

    @property
    def pattern(self):
        raise NotImplementedError()

    @property
    def metadata(self):
        return {field: self.__dict__[field] for field in METADATA_FIELDS}

    @property
    def name(self):
        return generate_filename(self.pattern, self.metadata)

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
    class Meta(BlobModel.Meta):
        unique_together = METADATA_FIELDS + ['dataset']

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='segmentations')

    @property
    def pattern(self):
        return self.dataset.segmentation_pattern


class Groomed(BlobModel):
    class Meta(BlobModel.Meta):
        unique_together = METADATA_FIELDS + ['dataset']

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='groomed')

    @property
    def pattern(self):
        return self.dataset.groomed_pattern


class ShapeModel(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    analyze = S3FileField()
    correspondence = S3FileField()
    transform = S3FileField()
    magic_number = models.IntegerField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='shape_models')


class Particles(BlobModel):
    class Meta(BlobModel.Meta):
        unique_together = METADATA_FIELDS + ['shape_model']

    shape_model = models.ForeignKey(ShapeModel, on_delete=models.CASCADE, related_name='particles')

    @property
    def pattern(self):
        return self.shape_model.dataset.particles_pattern
