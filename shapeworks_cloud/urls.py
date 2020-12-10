from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg2 import openapi
from drf_yasg2.views import get_schema_view
from rest_framework import permissions, routers

# from shapeworks_cloud.core.rest import ImageViewSet
# from shapeworks_cloud.core.views import GalleryView, image_summary
from shapeworks_cloud.core.views import (
    dataset_create,
    dataset_detail,
    dataset_edit,
    dataset_list,
    groomed_create,
    groomed_detail,
    groomed_edit,
    home,
    segmentation_create,
    segmentation_detail,
    segmentation_edit,
    shape_model_create,
    shape_model_detail,
    shape_model_edit,
)

router = routers.SimpleRouter()
# router.register(r'images', ImageViewSet)

# OpenAPI generation
schema_view = get_schema_view(
    openapi.Info(title='ShapeWorks Cloud', default_version='v1', description=''),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('api/v1/s3-upload/', include('s3_file_field.urls')),
    path('api/v1/', include(router.urls)),
    path('api/docs/redoc', schema_view.with_ui('redoc'), name='docs-redoc'),
    path('api/docs/swagger', schema_view.with_ui('swagger'), name='docs-swagger'),
    path('', home, name='home'),
    path('datasets/', dataset_list, name='dataset_list'),
    path('datasets/create/', dataset_create, name='dataset_create'),
    path('datasets/<pk>/', dataset_detail, name='dataset_detail'),
    path('datasets/<pk>/edit/', dataset_edit, name='dataset_edit'),
    path('datasets/<dataset_pk>/groomed/create/', groomed_create, name='groomed_create'),
    path('datasets/<dataset_pk>/groomed/<groomed_pk>/', groomed_detail, name='groomed_detail'),
    path('datasets/<dataset_pk>/groomed/<groomed_pk>/edit/', groomed_edit, name='groomed_edit'),
    path(
        'datasets/<dataset_pk>/segmentation/create/',
        segmentation_create,
        name='segmentation_create',
    ),
    path(
        'datasets/<dataset_pk>/segmentation/<segmentation_pk>/',
        segmentation_detail,
        name='segmentation_detail',
    ),
    path(
        'datasets/<dataset_pk>/segmentation/<segmentation_pk>/edit/',
        segmentation_edit,
        name='segmentation_edit',
    ),
    path(
        'datasets/<dataset_pk>/shape_model/create/', shape_model_create, name='shape_model_create'
    ),
    path(
        'datasets/<dataset_pk>/shape_model/<shape_model_pk>/',
        shape_model_detail,
        name='shape_model_detail',
    ),
    path(
        'datasets/<dataset_pk>/shape_model/<shape_model_pk>/edit/',
        shape_model_edit,
        name='shape_model_edit',
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
