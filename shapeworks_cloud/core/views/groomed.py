from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls.base import reverse

from shapeworks_cloud.core.forms import GroomedForm
from shapeworks_cloud.core.models import Dataset, Groomed


def groomed_detail(request, dataset_pk, groomed_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    groomed = get_object_or_404(Groomed, dataset__pk=dataset_pk, pk=groomed_pk)
    context = {
        'dataset': dataset,
        'groomed': groomed,
    }
    return render(request, 'groomed_detail.html', context)


@login_required
def groomed_create(request, dataset_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    if request.method == 'POST':
        # Create a new Groomed
        groomed = Groomed(dataset=dataset)
        form = GroomedForm(request.POST, instance=groomed)
        if form.is_valid():
            groomed.save()
            return HttpResponseRedirect(reverse('dataset_detail', args=(dataset.pk,)))
    else:
        form = GroomedForm()
    context = {
        'form': form,
        'dataset': dataset,
    }
    return render(request, 'groomed_create.html', context)


@login_required
def groomed_edit(request, dataset_pk, groomed_pk):
    dataset = get_object_or_404(Dataset, pk=dataset_pk)
    groomed = get_object_or_404(Groomed, dataset__pk=dataset_pk, pk=groomed_pk)
    if request.method == 'POST':
        # Edit an existing Groomed
        form = GroomedForm(request.POST, instance=groomed)
        if form.is_valid():
            form.instance.save()
            return HttpResponseRedirect(reverse('groomed_detail', args=(dataset.pk, groomed.pk)))
    else:
        form = GroomedForm(instance=groomed)
    context = {
        'form': form,
        'dataset': dataset,
        'groomed': groomed,
    }
    return render(request, 'groomed_edit.html', context)
