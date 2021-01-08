from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse

from shapeworks_cloud.core.forms import SegmentationForm
from shapeworks_cloud.core.models import Dataset, Segmentation


def segmentation_detail(request, dataset_pk, segmentation_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    segmentation = get_object_or_404(Segmentation, dataset__pk=dataset_pk, pk=segmentation_pk)
    context = {
        'dataset': dataset,
        'segmentation': segmentation,
    }
    return render(request, 'segmentation_detail.html', context)


@login_required
def segmentation_create(request, dataset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if request.method == 'POST':
        # Create a new Segmentation
        form = SegmentationForm(request.POST)
        if form.is_valid():
            segmentation = form.instance
            segmentation.dataset = dataset
            segmentation.save()
            return HttpResponseRedirect(reverse('dataset_detail', args=(dataset.pk,)))
    else:
        form = SegmentationForm()
    context = {
        'form': form,
        'dataset': dataset,
    }
    return render(request, 'segmentation_create.html', context)


@login_required
def segmentation_edit(request, dataset_pk, segmentation_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    segmentation = get_object_or_404(Segmentation, dataset__pk=dataset_pk, pk=segmentation_pk)
    if request.method == 'POST':
        # Edit an existing Segmentation
        form = SegmentationForm(request.POST, instance=segmentation)
        if form.is_valid():
            form.instance.save()
            return HttpResponseRedirect(
                reverse('segmentation_detail', args=(dataset.pk, segmentation.pk))
            )
    else:
        form = SegmentationForm(instance=segmentation)
    context = {
        'form': form,
        'dataset': dataset,
        'segmentation': segmentation,
    }
    return render(request, 'segmentation_edit.html', context)
