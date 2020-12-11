from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse

from shapeworks_cloud.core.forms import ParticlesForm, ShapeModelForm
from shapeworks_cloud.core.models import Dataset, ShapeModel, Particles


def shape_model_detail(request, dataset_pk, shape_model_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    shape_model = get_object_or_404(ShapeModel, dataset__pk=dataset_pk, pk=shape_model_pk)

    paginator = Paginator(shape_model.particles.order_by('name'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'dataset': dataset,
        'shape_model': shape_model,
        'page_obj': page_obj,
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
            return HttpResponseRedirect(reverse('dataset_detail', args=(dataset.pk,)))
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
        form = ShapeModelForm(
            request.POST,
            initial={
                'analyze': shape_model.analyze,
                'correspondence': shape_model.correspondence,
                'transform': shape_model.transform,
            },
        )
        if not form.fields['analyze']:
            form.fields.analyze = shape_model.analyze
        if not form.fields['correspondence']:
            form.fields.correspondence = shape_model.correspondence
        if not form.fields['transform']:
            form.fields.transform = shape_model.transform
        if form.is_valid():
            shape_model.dataset = dataset
            shape_model.name = form.instance.name
            shape_model.analyze = form.instance.analyze
            shape_model.correspondence = form.instance.correspondence
            shape_model.transform = form.instance.transform
            shape_model.save()
            return HttpResponseRedirect(
                reverse('shape_model_detail', args=(dataset.pk, shape_model.pk))
            )
    else:
        form = ShapeModelForm(instance=shape_model)
    context = {
        'form': form,
        'dataset': dataset,
        'shape_model': shape_model,
    }
    return render(request, 'shape_model_edit.html', context)
