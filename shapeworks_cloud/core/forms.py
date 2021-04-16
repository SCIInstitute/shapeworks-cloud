from django import forms


class GroomedDatasetForm(forms.Form):
    name = forms.CharField()
    images = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
