from django import forms
from django.core.exceptions import ValidationError

from shapeworks_cloud.core.metadata import METADATA_FIELDS, validate_metadata
from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name', 'groomed_pattern', 'segmentation_pattern', 'particles_pattern']

    def _clean_pattern(self, pattern_name, queryset):
        pattern = self.cleaned_data[pattern_name]
        try:
            for instance in queryset.all():
                validate_metadata(pattern, instance.metadata)
        except ValueError as e:
            raise ValidationError(e)
        return pattern

    def clean_groomed_pattern(self):
        return self._clean_pattern('groomed_pattern', self.instance.groomed)

    def clean_segmentation_pattern(self):
        return self._clean_pattern('segmentation_pattern', self.instance.segmentations)

    def clean_particles_pattern(self):
        return self._clean_pattern(
            'particles_pattern', Particles.objects.filter(shape_model__dataset=self.instance)
        )


class BlobForm(forms.ModelForm):
    class Meta:
        abstract = True
        fields = METADATA_FIELDS + ['blob']


class SegmentationForm(BlobForm):
    class Meta(BlobForm.Meta):
        model = Segmentation


class GroomedForm(BlobForm):
    class Meta(BlobForm.Meta):
        model = Groomed


class ShapeModelForm(forms.ModelForm):
    class Meta(BlobForm.Meta):
        model = ShapeModel
        fields = ['name', 'analyze', 'correspondence', 'transform', 'magic_number']


class ParticlesForm(BlobForm):
    class Meta(BlobForm.Meta):
        model = Particles
