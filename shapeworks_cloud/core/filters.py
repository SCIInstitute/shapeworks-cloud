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
