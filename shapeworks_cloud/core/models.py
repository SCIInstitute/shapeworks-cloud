from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField


class GroomedDataset(TimeStampedModel, models.Model):
    """A set of groomed images used to initialize a project."""

    name = models.CharField(max_length=255, unique=True)

    @property
    def num_segmentations(self):
        return self.segmentations.count


class GroomedSegmentation(TimeStampedModel, models.Model):
    """
    A preprocessed image used an in input to shapeworks optimization.

    This model represents a preprocessed 3D raster typically in the form
    of an nrrd file stored in the blob.  The mesh is a VTK polydata structure
    representing the 0-contour of the raster.
    """

    # The original file name
    name = models.CharField(max_length=255)

    # The contents of the nrrd file
    blob = S3FileField()

    # The 0-contour of the image represented as a vtp file
    mesh = S3FileField(null=True)

    dataset = models.ForeignKey(
        GroomedDataset, on_delete=models.CASCADE, related_name='segmentations'
    )

    # The index in the dataset to provide consistent ordering
    index = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(index__gte=0), name='chk_index_gte_0'),
            models.UniqueConstraint(fields=['dataset', 'index'], name='unq_dataset_index'),
            models.UniqueConstraint(fields=['dataset', 'name'], name='unq_dataset_name'),
        ]
        ordering = ['dataset', 'index']

    def save(self, *args, **kwargs):
        from .tasks import generate_segmentation_mesh

        super().save(*args, **kwargs)

        update_fields = kwargs.get('update_fields', [])

        # We don't want to re-run mesh generation
        if self.mesh is None or 'mesh' not in update_fields:
            generate_segmentation_mesh.delay(self.pk)


class Project(TimeStampedModel, models.Model):
    """The top-level entity in a shapeworks analysis."""

    name = models.CharField(max_length=255, unique=True)
    groomed_dataset = models.ForeignKey(GroomedDataset, on_delete=models.CASCADE, related_name='+')


class ShapeModel(TimeStampedModel, models.Model):
    local = S3FileField()
    world = S3FileField()


class Optimization(TimeStampedModel, models.Model):
    """
    This represents an optimization run on a project.

    The intent of the model is to provide full provenance of the optimization run as well as the
    parent entity for generated point models (the output of the optimization).
    """

    # This model shares a primary key with the referenced project
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='optimizations',
    )

    # What version of shapeworks this was run on for provenance
    shapeworks_version = models.CharField(max_length=255, default='6.0.0')

    # The final output from the optimization (null until complete)
    shape_model = models.ForeignKey(ShapeModel, on_delete=models.CASCADE, null=True)

    # Job status attributes (should be manipulated by the celery task)
    running = models.BooleanField(default=False)

    # Indicates an error was raised during the optimization
    error = models.BooleanField(default=False)

    @property
    def queued(self) -> bool:
        return not self.error and self.shape_model is None and not self.running

    @property
    def finished(self) -> bool:
        return self.shape_model is not None and not self.running


class OptimizationParameters(models.Model):
    """
    This represents the set of parameters passed to the shapeworks cli.

    Something more fancy might need to be done if the parameter set changes with shapeworks version.
    Perhaps we could make multiple tables for the different parameter schemas, or encode the
    differences in jsonfields.  We'll cross that bridge when we come to it.
    """

    class DomainType(models.TextChoices):
        IMAGE = 'image'
        MESH = 'mesh'

    optimization = models.OneToOneField(
        Optimization,
        on_delete=models.CASCADE,
        related_name='parameters',
        primary_key=True,
    )

    # parameters with defaults from ellipsoid.py
    number_of_particles = models.IntegerField(default=128)
    use_normals = models.BooleanField(default=False)
    normal_weight = models.FloatField(default=10.0)
    checkpointing_interval = models.IntegerField(default=1000)
    # keep_checkpoints = True, otherwise we can't read it in the celery task
    iterations_per_split = models.IntegerField(default=1000)
    optimization_iterations = models.IntegerField(default=1000)
    starting_regularization = models.FloatField(default=10.0)
    ending_regularization = models.FloatField(default=1.0)
    recompute_regularization_interval = models.IntegerField(default=1)
    domains_per_shape = models.IntegerField(default=1)
    domain_type = models.CharField(
        max_length=16, choices=DomainType.choices, default=DomainType.IMAGE
    )
    relative_weighting = models.FloatField(default=1.0)
    initial_relative_weighting = models.FloatField(default=1.0)
    procrustes_interval = models.IntegerField(default=0)
    procrustes_scaling = models.BooleanField(default=False)
    # save_init_splits = False, don't know if we need these
    # verbosity = 0, probably don't need to expose this to the user


class OptimizationCheckpoint(models.Model):
    """A set of shape models associated with a single iteration of an optimization."""

    blob = S3FileField()
    split = models.IntegerField()
    iteration = models.IntegerField()
    number_of_particles = models.IntegerField()

    optimization = models.ForeignKey(
        Optimization,
        on_delete=models.CASCADE,
        related_name='checkpoints',
    )

    shape_model = models.ForeignKey(ShapeModel, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['optimization', 'iteration'], name='unq_optimization_iteration'
            ),
        ]
