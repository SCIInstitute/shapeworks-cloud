from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from shapeworks_cloud.core.forms import AssetForm, DatasetForm
from shapeworks_cloud.core.models import Asset, Dataset


def dataset_list(request):
    paginator = Paginator(Dataset.objects.order_by('created'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'dataset_list.html', context)


def dataset_detail(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk)

    segmentation_paginator = Paginator(
        dataset.files.filter(asset_type='segmentation').order_by('name'), 10
    )
    segmentation_page_number = request.GET.get('segmentation_page')
    segmentation_page_obj = segmentation_paginator.get_page(segmentation_page_number)

    groomed_paginator = Paginator(dataset.files.filter(asset_type='groomed').order_by('name'), 10)
    groomed_page_number = request.GET.get('groomed_page')
    groomed_page_obj = groomed_paginator.get_page(groomed_page_number)

    shape_model_paginator = Paginator(
        dataset.files.filter(asset_type='shape_model').order_by('name'), 10
    )
    shape_model_page_number = request.GET.get('shape_model_page')
    shape_model_page_obj = shape_model_paginator.get_page(shape_model_page_number)

    context = {
        'dataset': dataset,
        'segmentation_page_obj': segmentation_page_obj,
        'groomed_page_obj': groomed_page_obj,
        'shape_model_page_obj': shape_model_page_obj,
    }
    return render(request, 'dataset_detail.html', context)


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


def asset_detail(request, dataset_pk, asset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    asset = get_object_or_404(Asset, dataset__pk=dataset_pk, pk=asset_pk)
    context = {
        'dataset': dataset,
        'asset': asset,
    }
    return render(request, 'asset_detail.html', context)


def asset_create(request, dataset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if request.method == 'POST':
        # Create a new Asset
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.instance
            asset.dataset = dataset
            asset.save()
            return HttpResponseRedirect(f'/datasets/{dataset_pk}/')
    else:
        form = AssetForm()
    context = {
        'form': form,
        'dataset': dataset,
    }
    return render(request, 'asset_create.html', context)


def asset_edit(request, dataset_pk, asset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    asset = get_object_or_404(Asset, dataset__pk=dataset_pk, pk=asset_pk)
    if request.method == 'POST':
        # Create a new Asset
        form = AssetForm(request.POST, initial={'blob': asset.blob})
        print(form.fields['blob'])
        if not form.fields['blob']:
            form.fields.blob = asset.blob
        if form.is_valid():
            print('valid')
            asset.dataset = dataset
            asset.name = form.instance.name
            asset.blob = form.instance.blob
            asset.asset_type = form.instance.asset_type
            asset.save()
            return HttpResponseRedirect(f'/datasets/{dataset_pk}/files/{asset_pk}/')
        print('doone')
    else:
        form = AssetForm(instance=asset)
    context = {
        'form': form,
        'dataset': dataset,
        'asset': asset,
    }
    return render(request, 'asset_edit.html', context)


def home(request):
    return render(request, 'index.html')
