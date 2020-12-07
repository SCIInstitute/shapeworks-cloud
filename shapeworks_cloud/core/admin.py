from django.contrib import admin

from shapeworks_cloud.core.models import Asset, Dataset


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


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'blob', 'created']
    list_display_links = ['id', 'name']
    list_filter = [
        ('created', admin.DateFieldListFilter),
        'dataset',
    ]
    list_select_related = True
    # list_select_related = ['owner']

    search_fields = ['name']

    fields = ['name', 'blob', 'dataset', 'created', 'modified']
    readonly_fields = ['created', 'modified']
