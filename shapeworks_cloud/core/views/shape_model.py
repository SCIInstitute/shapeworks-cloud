from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from shapeworks_cloud.core.forms import ShapeModelBlobForm, ShapeModelForm
from shapeworks_cloud.core.models import Dataset, ShapeModel, ShapeModelBlob


def shape_model_detail(request, dataset_pk, shape_model_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    shape_model = get_object_or_404(ShapeModel, dataset__pk=dataset_pk, pk=shape_model_pk)
    context = {
        'dataset': dataset,
        'shape_model': shape_model,
    }
    return render(request, 'shape_model_detail.html', context)


@login_required
def shape_model_create(request, dataset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if request.method == 'POST':
        # Create a new ShapeModel
        form = ShapeModelForm(request.POST)
        if form.is_valid():
            shape_model = form.instance
            shape_model.dataset = dataset
            shape_model.save()
            return HttpResponseRedirect(f'/datasets/{dataset_pk}/')
    else:
        form = ShapeModelForm()
    context = {
        'form': form,
        'dataset': dataset,
    }
    return render(request, 'shape_model_create.html', context)


@login_required
def shape_model_edit(request, dataset_pk, shape_model_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    shape_model = get_object_or_404(ShapeModel, dataset__pk=dataset_pk, pk=shape_model_pk)
    if request.method == 'POST':
        # Edit an existing ShapeModel
        form = ShapeModelForm(request.POST, initial={'blob': shape_model.blob})
        if not form.fields['blob']:
            form.fields.blob = shape_model.blob
        if form.is_valid():
            shape_model.dataset = dataset
            shape_model.name = form.instance.name
            shape_model.blob = form.instance.blob
            shape_model.save()
            return HttpResponseRedirect(f'/datasets/{dataset_pk}/shape_model/{shape_model_pk}/')
    else:
        form = ShapeModelForm(instance=shape_model)
    context = {
        'form': form,
        'dataset': dataset,
        'shape_model': shape_model,
    }
    return render(request, 'shape_model_edit.html', context)
