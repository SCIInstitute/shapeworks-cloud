from django_filters import FilterSet, ModelChoiceFilter

from . import models


class DatasetFilter(FilterSet):
    class Meta:
        model = models.Dataset
        fields = ['name']


class SubjectFilter(FilterSet):
    dataset = ModelChoiceFilter(queryset=models.Dataset.objects.all())

    class Meta:
        model = models.Subject
        fields = ['dataset']


class ProjectFilter(FilterSet):
    dataset = ModelChoiceFilter(queryset=models.Dataset.objects.all())

    class Meta:
        model = models.Project
        fields = ['dataset']


class SegmentationFilter(FilterSet):
    subject = ModelChoiceFilter(queryset=models.Subject.objects.all())

    class Meta:
        models = models.Segmentation
        fields = ['subject']


class MeshFilter(FilterSet):
    subject = ModelChoiceFilter(queryset=models.Subject.objects.all())

    class Meta:
        models = models.Mesh
        fields = ['subject']


class ImageFilter(FilterSet):
    subject = ModelChoiceFilter(queryset=models.Subject.objects.all())

    class Meta:
        models = models.Image
        fields = ['subject']


class GroomedSegmentationFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())
    segmentation = ModelChoiceFilter(queryset=models.Segmentation.objects.all())

    class Meta:
        models = models.GroomedSegmentation
        fields = ['project', 'segmentation']


class GroomedMeshFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())
    mesh = ModelChoiceFilter(queryset=models.Mesh.objects.all())

    class Meta:
        models = models.GroomedMesh
        fields = ['project', 'mesh']


class OptimizedParticlesFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())
    original_segmentation = ModelChoiceFilter(
        field_name='groomed_segmentation__segmentation',
        queryset=models.Segmentation.objects.all(),
    )
    original_mesh = ModelChoiceFilter(
        field_name='groomed_mesh__mesh',
        queryset=models.Mesh.objects.all(),
    )
    groomed_segmentation = ModelChoiceFilter(queryset=models.GroomedSegmentation.objects.all())
    groomed_mesh = ModelChoiceFilter(queryset=models.GroomedMesh.objects.all())

    class Meta:
        models = models.OptimizedParticles
        fields = [
            'shape_model',
            'groomed_segmentation',
            'groomed_mesh',
            'original_segmentation',
            'original_mesh',
        ]


class ReconstructedSampleFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())

    class Meta:
        models = models.ReconstructedSample
        fields = ['project']
