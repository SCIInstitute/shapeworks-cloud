from django_filters import FilterSet, ModelChoiceFilter

from . import models


class SubjectFilter(FilterSet):
    dataset = ModelChoiceFilter(queryset=models.Dataset.objects.all())

    class Meta:
        model = models.Subject
        fields = ['dataset']


class SegmentationFilter(FilterSet):
    subject = ModelChoiceFilter(queryset=models.Subject.objects.all())

    class Meta:
        models = models.Segmentation
        fields = ['subject']


class GroomedSegmentationFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())
    segmentation = ModelChoiceFilter(queryset=models.Segmentation.objects.all())

    class Meta:
        models = models.GroomedSegmentation
        fields = ['project', 'segmentation']


class OptimizedShapeModelFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())

    class Meta:
        models = models.OptimizedShapeModel
        fields = ['project']


class OptimizedParticles(FilterSet):
    shape_model = ModelChoiceFilter(queryset=models.OptimizedShapeModel.objects.all())
    groomed_segmentation = ModelChoiceFilter(queryset=models.GroomedSegmentation.objects.all())

    class Meta:
        models = models.OptimizedParticles
        fields = ['shape_model', 'groomed_segmentation']
