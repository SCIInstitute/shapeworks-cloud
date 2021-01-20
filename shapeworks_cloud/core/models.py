from django.core.exceptions import ValidationError
from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .metadata import METADATA_FIELDS, generate_filename, validate_metadata


class FormattedSizeMixin:
    @property
    def formatted_size(self, base=1024, unit='B'):
        size = self.size
        if size < base:
            return f'{size} {unit}'
        units = ['', 'K', 'M', 'G', 'T']
        i = 0
        while i < 5 and size >= base:
            size /= base
            i += 1
        return f'{size:.2f} {units[i]}{unit}'


class Dataset(FormattedSizeMixin, TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    groomed_pattern = models.CharField(max_length=255, null=False, blank=True, default='')
    segmentation_pattern = models.CharField(max_length=255, null=False, blank=True, default='')
    particles_pattern = models.CharField(max_length=255, null=False, blank=True, default='')

    @property
    def num_segmentations(self):
        return self.segmentations.count()

    @property
    def num_groomed(self):
        return self.groomed.count()

    @property
    def num_shape_models(self):
        return self.shape_models.count()

    @property
    def size(self):
        return (
            sum([segmentation.size for segmentation in self.segmentations.all()])
            + sum([groomed.size for groomed in self.groomed.all()])
            + sum([shape_model.size for shape_model in self.shape_models.all()])
        )


class BlobModel(FormattedSizeMixin, TimeStampedModel, models.Model):
    blob = S3FileField()

    # Each member of METADATA_FIELDS has a corresponding field here
    subject = models.IntegerField(null=False)
    particle_type = models.CharField(
        null=False,
        blank=True,
        default='',
        max_length=12,
        choices=[
            ('', ''),
            ('local', 'local'),
            ('world', 'world'),
            ('wptsFeatures', 'wptsFeatures'),
        ],
    )
    chirality = models.CharField(
        null=False,
        blank=True,
        default='',
        max_length=1,
        choices=[
            ('', ''),
            ('L', 'Left'),
            ('R', 'Right'),
        ],
    )
    extension = models.CharField(
        null=False,
        blank=True,
        default='',
        max_length=9,
        choices=[
            ('', ''),
            ('nrrd', 'nrrd'),
            ('vtk', 'vtk'),
            ('ply', 'ply'),
            ('particles', 'particles'),
        ],
    )
    grooming_steps = models.CharField(null=False, blank=True, default='', max_length=255)

    class Meta:
        abstract = True

    def clean(self, *args, **kwargs):
        try:
            validate_metadata(self.pattern, self.metadata)
        except ValueError as e:
            raise ValidationError(e)

    def validate_unique(self, *args, **kwargs):
        # TODO Forms do not populate foreign keys, and clean() requires the pattern, which is
        # stored on the dataset. The dataset is injected in the view, but is still set as excluded
        # by the form validation, so we must override that setting here.
        super().validate_unique(exclude=['id', 'created', 'modified'])

    @property
    def pattern(self):
        raise NotImplementedError()

    @property
    def all_metadata(self):
        return {field: self.__dict__[field] for field in METADATA_FIELDS}

    @property
    def metadata(self):
        return {field: value for field, value in self.all_metadata.items() if value != ''}

    @property
    def metadata_values(self):
        """Concisely summarize all metadata for display in a table."""
        return ','.join([value for field, value in self.metadata.items() if field != 'subject'])

    @property
    def name(self):
        return generate_filename(self.pattern, self.all_metadata)

    @property
    def size(self):
        return self.blob.size

    @property
    def formatted_size(self, base=1024, unit='B'):
        size = self.size
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
        constraints = [
            models.UniqueConstraint(
                fields=METADATA_FIELDS + ['dataset'], name='unique_segmentation'
            )
        ]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='segmentations')

    @property
    def pattern(self):
        return self.dataset.segmentation_pattern


class Groomed(BlobModel):
    class Meta(BlobModel.Meta):
        constraints = [
            models.UniqueConstraint(fields=METADATA_FIELDS + ['dataset'], name='unique_groomed')
        ]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='groomed')

    @property
    def pattern(self):
        return self.dataset.groomed_pattern


class ShapeModel(FormattedSizeMixin, TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    analyze = S3FileField()
    correspondence = S3FileField()
    transform = S3FileField()
    magic_number = models.IntegerField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='shape_models')

    @property
    def num_particles(self):
        return self.particles.count()

    @property
    def size(self):
        return sum([particles.size for particles in self.particles.all()])


class Particles(BlobModel):
    class Meta(BlobModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=METADATA_FIELDS + ['shape_model'], name='unique_particles'
            )
        ]

    shape_model = models.ForeignKey(ShapeModel, on_delete=models.CASCADE, related_name='particles')

    @property
    def pattern(self):
        return self.shape_model.dataset.particles_pattern
