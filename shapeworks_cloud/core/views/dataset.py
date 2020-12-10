from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from shapeworks_cloud.core.forms import (
    DatasetForm,
    GroomedForm,
    SegmentationForm,
    ShapeModelBlobForm,
    ShapeModelForm,
)
from shapeworks_cloud.core.models import Dataset, Groomed, Segmentation, ShapeModel, ShapeModelBlob


def dataset_list(request):
    paginator = Paginator(Dataset.objects.order_by('created'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'dataset_list.html', context)


def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)

    segmentation_paginator = Paginator(dataset.segmentations.order_by('name'), 10)
    segmentation_page_number = request.GET.get('segmentation_page')
    segmentation_page_obj = segmentation_paginator.get_page(segmentation_page_number)

    groomed_paginator = Paginator(dataset.groomed.order_by('name'), 10)
    groomed_page_number = request.GET.get('groomed_page')
    groomed_page_obj = groomed_paginator.get_page(groomed_page_number)

    shape_model_paginator = Paginator(dataset.shape_models.order_by('name'), 10)
    shape_model_page_number = request.GET.get('shape_model_page')
    shape_model_page_obj = shape_model_paginator.get_page(shape_model_page_number)

    context = {
        'dataset': dataset,
        'segmentation_page_obj': segmentation_page_obj,
        'groomed_page_obj': groomed_page_obj,
        'shape_model_page_obj': shape_model_page_obj,
    }
    return render(request, 'dataset_detail.html', context)


@login_required
def dataset_create(request):
    if request.method == 'POST':
        # Create a new Dataset
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset = form.instance
            dataset.save()
            return HttpResponseRedirect(f'/datasets/{dataset.pk}')
    else:
        form = DatasetForm()
    return render(request, 'dataset_create.html', {'form': form})


@login_required
def dataset_edit(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)
    if request.method == 'POST':
        # Overwrite the Dataset
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset.name = form.instance.name
            dataset.save()
            return HttpResponseRedirect(f'/datasets/{dataset.pk}/')
    else:
        form = DatasetForm(instance=dataset)
    context = {
        'form': form,
        'dataset': dataset,
    }
    return render(request, 'dataset_edit.html', context)