from django_filters import FilterSet, ModelChoiceFilter

from . import models


class OptimizationFilter(FilterSet):
    project = ModelChoiceFilter(queryset=models.Project.objects.all())

    class Meta:
        model = models.Optimization
        fields = ['project']
