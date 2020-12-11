from django import forms

from shapeworks_cloud.core.models import Dataset, Groomed, Segmentation, ShapeModel, Particles


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name']


class SegmentationForm(forms.ModelForm):
    class Meta:
        model = Segmentation
        fields = ['name', 'blob']


class GroomedForm(forms.ModelForm):
    class Meta:
        model = Groomed
        fields = ['name', 'blob']


class ShapeModelForm(forms.ModelForm):
    class Meta:
        model = ShapeModel
        fields = ['name', 'analyze', 'correspondence', 'transform', 'magic_number']


class ParticlesForm(forms.ModelForm):
    class Meta:
        model = Particles
        fields = ['name', 'blob']
