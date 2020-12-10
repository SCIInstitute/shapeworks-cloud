from django.contrib import admin

from shapeworks_cloud.core.models import Dataset, Groomed, Segmentation, ShapeModel, ShapeModelBlob


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created']
    list_display_links = ['id', 'name']
    list_filter = [
        ('created', admin.DateFieldListFilter),
    ]
    list_select_related = True
    # list_select_related = ['owner']

    search_fields = ['name']

    fields = ['name', 'created', 'modified']
    readonly_fields = ['created', 'modified']


class BlobAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'blob', 'created']
    list_display_links = ['id', 'name']

    list_select_related = True
    # list_select_related = ['owner']

    search_fields = ['name']

    readonly_fields = ['created', 'modified']


@admin.register(Segmentation)
class SegmentationAdmin(BlobAdmin):
    list_filter = [
        ('created', admin.DateFieldListFilter),
        'dataset',
    ]
    fields = ['name', 'blob', 'dataset', 'created', 'modified']


@admin.register(Groomed)
class GroomedAdmin(BlobAdmin):
    list_filter = [
        ('created', admin.DateFieldListFilter),
        'dataset',
    ]
    fields = ['name', 'blob', 'dataset', 'created', 'modified']


@admin.register(ShapeModel)
class ShapeModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'dataset', 'created']
    list_display_links = ['id', 'name']
    list_filter = [
        ('created', admin.DateFieldListFilter),
    ]
    list_select_related = True
    # list_select_related = ['owner']

    search_fields = ['name']

    fields = [
        'name',
        'analyze',
        'correspondence',
        'transform',
        'magic_number',
        'dataset',
        'created',
        'modified',
    ]
    readonly_fields = ['created', 'modified']


@admin.register(ShapeModelBlob)
class ShapeModelBlobAdmin(BlobAdmin):
    list_filter = [
        ('created', admin.DateFieldListFilter),
        'shape_model',
    ]
    fields = ['name', 'blob', 'shape_model', 'created', 'modified']
