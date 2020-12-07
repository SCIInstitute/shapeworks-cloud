from django import forms

from shapeworks_cloud.core.models import Asset, Dataset


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name']


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'blob', 'asset_type']
