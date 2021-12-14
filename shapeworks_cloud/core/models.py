from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField


class Dataset(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255, unique=True)

    file = S3FileField(null=True)
    # FK to another table?
    license = models.TextField()
    description = models.TextField()
    acknowledgement = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, default='')

    # FK to another table?
    contributors = models.TextField(blank=True, default='')

    # FK to another table?
    publications = models.TextField(blank=True, default='')


class Subject(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='subjects')


class Segmentation(models.Model):
    file = S3FileField()
    anatomy_type = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='segmentations')


class Mesh(models.Model):
    file = S3FileField()
    anatomy_type = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='meshes')


class Image(models.Model):
    file = S3FileField()
    modality = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='images')


class Project(TimeStampedModel, models.Model):
    file = S3FileField()
    keywords = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='projects')


class GroomedSegmentation(models.Model):
    # The contents of the nrrd file
    file = S3FileField()

    # represent these in raw form?
    pre_cropping = S3FileField(null=True)
    pre_alignment = S3FileField(null=True)

    segmentation = models.OneToOneField(
        Segmentation,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='groomed',
    )

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='groomed_segmentations'
    )


class GroomedMesh(models.Model):
    # The contents of the nrrd file
    file = S3FileField()

    # represent these in raw form?
    pre_cropping = S3FileField(null=True)
    pre_alignment = S3FileField(null=True)

    mesh = models.OneToOneField(
        Mesh,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='groomed',
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='groomed_meshes')


class OptimizedShapeModel(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='optimized_shape_models',
    )
    parameters = models.JSONField(default=dict)


class OptimizedParticles(models.Model):
    world = S3FileField()
    local = S3FileField()
    transform = S3FileField()

    shape_model = models.ForeignKey(
        OptimizedShapeModel,
        on_delete=models.CASCADE,
        related_name='particles',
    )
    groomed_segmentation = models.ForeignKey(
        GroomedSegmentation,
        on_delete=models.CASCADE,
        related_name='+',
        blank=True,
        null=True,
    )
    groomed_mesh = models.ForeignKey(
        GroomedMesh,
        on_delete=models.CASCADE,
        related_name='+',
        blank=True,
        null=True,
    )


class OptimizedSurfaceReconstructionMeta(models.Model):
    method = models.CharField(max_length=255)  # TODO: Should be choices
    reconstruction_params = S3FileField()
    template_reconstruction = S3FileField()

    shape_model = models.ForeignKey(
        OptimizedShapeModel,
        on_delete=models.CASCADE,
        related_name='+',
    )


class OptimizedSurfaceReconstruction(models.Model):
    particles = models.OneToOneField(
        OptimizedParticles,
        on_delete=models.CASCADE,
        related_name='surface_reconstruction',
        primary_key=True,
    )
    sample_reconstruction = S3FileField()


class OptimizedPCAModel(models.Model):
    shape_model = models.OneToOneField(
        OptimizedShapeModel,
        on_delete=models.CASCADE,
        related_name='pca_model',
        primary_key=True,
    )

    mean_particles = S3FileField()
    pca_modes = S3FileField()
    eigen_spectrum = S3FileField()


# TODO: checkpoints... what about pca model reference?
