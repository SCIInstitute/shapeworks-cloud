from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg2 import openapi
from drf_yasg2.views import get_schema_view
from rest_framework import permissions, routers

# from shapeworks_cloud.core.rest import ImageViewSet
# from shapeworks_cloud.core.views import GalleryView, image_summary
from shapeworks_cloud.core.views import (
    asset_create,
    asset_detail,
    asset_edit,
    dataset_create,
    dataset_detail,
    dataset_edit,
    dataset_list,
    home,
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
    path('api/s3-upload/', include('s3_file_field.urls')),
    path('api/v1/', include(router.urls)),
    path('api/docs/redoc', schema_view.with_ui('redoc'), name='docs-redoc'),
    path('api/docs/swagger', schema_view.with_ui('swagger'), name='docs-swagger'),
    path('', home, name='home'),
    path('datasets/', dataset_list, name='dataset_list'),
    path('datasets/create/', dataset_create, name='dataset_create'),
    path('datasets/<pk>/', dataset_detail, name='dataset_detail'),
    path('datasets/<pk>/edit/', dataset_edit, name='dataset_edit'),
    path('datasets/<dataset_pk>/files/create/', asset_create, name='asset_create'),
    path('datasets/<dataset_pk>/files/<asset_pk>/', asset_detail, name='asset_detail'),
    path('datasets/<dataset_pk>/files/<asset_pk>/edit/', asset_edit, name='asset_edit'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
