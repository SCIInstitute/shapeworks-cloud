import json

from django.core.files.base import ContentFile
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

    def get_contents(self, project=None):
        ret = []
        if not project:
            project = Project.objects.filter(dataset=self).first()

        def truncate_filename(filename):
            return filename.split('/')[-1]

        def record_shape(shape, groomed, particles):
            ret.append(
                {
                    'name': shape.subject.name,
                    'shape_1': truncate_filename(shape.file.name),
                    'groomed_1': 'groomed/' + truncate_filename(groomed.file.name),
                    'local_particles_1': 'particles/' + truncate_filename(particles.local.name),
                    'world_particles_1': 'particles/' + truncate_filename(particles.world.name),
                    'alignment_1': '',
                    'procrustes_1': '',
                }
            )

        for shape in Segmentation.objects.filter(subject__dataset=self):
            groomed = GroomedSegmentation.objects.get(segmentation=shape, project=project)
            particles = OptimizedParticles.objects.get(
                groomed_segmentation=groomed, project=project
            )
            record_shape(shape, groomed, particles)
        for shape in Mesh.objects.filter(subject__dataset=self):
            groomed = GroomedMesh.objects.get(mesh=shape, project=project)
            particles = OptimizedParticles.objects.get(groomed_mesh=groomed, project=project)
            record_shape(shape, groomed, particles)
        return ret


class Subject(TimeStampedModel, models.Model):
    name = models.CharField(max_length=255)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='subjects')


class Segmentation(TimeStampedModel, models.Model):
    file = S3FileField()
    anatomy_type = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='segmentations')


class Mesh(TimeStampedModel, models.Model):
    file = S3FileField()
    anatomy_type = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='meshes')


class Image(TimeStampedModel, models.Model):
    file = S3FileField()
    modality = models.CharField(max_length=255)  # choices?
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='images')


class CachedAnalysisModePCA(models.Model):
    pca_value = models.FloatField()
    lambda_value = models.FloatField()
    file = S3FileField()


class CachedAnalysisMode(models.Model):
    mode = models.IntegerField()
    eigen_value = models.FloatField()
    explained_variance = models.FloatField()
    cumulative_explained_variance = models.FloatField()
    pca_values = models.ManyToManyField(CachedAnalysisModePCA)


class CachedAnalysis(TimeStampedModel, models.Model):
    mean_shape = S3FileField()
    modes = models.ManyToManyField(CachedAnalysisMode)
    charts = models.JSONField()


class Project(TimeStampedModel, models.Model):
    file = S3FileField()
    keywords = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='projects')
    last_cached_analysis = models.ForeignKey(CachedAnalysis, on_delete=models.PROTECT, null=True)

    def create_new_file(self):
        file_contents = {
            'data': self.dataset.get_contents(self),
            'groom': {},
            'optimize': {},
        }
        self.file.save('project.swproj', ContentFile(json.dumps(file_contents).encode()))


class GroomedSegmentation(TimeStampedModel, models.Model):
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


class GroomedMesh(TimeStampedModel, models.Model):
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


class OptimizedParticles(TimeStampedModel, models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    world = S3FileField()
    local = S3FileField()
    transform = S3FileField()
    constraints = S3FileField(null=True)

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
