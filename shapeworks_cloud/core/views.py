from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render


def home(request: HttpRequest):
    return render(request, 'index.html')


@login_required
def groomed_dataset_create(request: HttpRequest):
    return render(request, 'groomed_dataset_create.html', {})


def groomed_dataset_list(request: HttpRequest):
    return render(request, 'groomed_dataset_list.html', {})


def groomed_dataset_detail(request: HttpRequest):
    return render(request, 'groomed_dataset_detail', {})
