from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_extensions.routers import ExtendedSimpleRouter

from shapeworks_cloud.core import rest, views

router = ExtendedSimpleRouter()
router.register('datasets', rest.DatasetViewSet, basename='dataset')
router.register('subjects', rest.SubjectViewSet, basename='subject')
router.register('segmentations', rest.SegmentationViewSet, basename='segmentation')
router.register('meshes', rest.MeshViewSet, basename='mesh')
router.register('projects', rest.ProjectViewSet, basename='project')
router.register(
    'groomed-segmentations', rest.GroomedSegmentationViewSet, basename='groomed_segmentation'
)
router.register(
    'groomed-meshes', rest.GroomedMeshViewSet, basename='groomed_mesh'
)
router.register(
    'optimized-shape-models', rest.OptimizedShapeModelViewSet, basename='optimized_shape_model'
)
router.register(
    'optimized-particles', rest.OptimizedParticlesViewSet, basename='optimized_particles'
)
router.register(
    'optimized-pca-model', rest.OptimizedPCAModelViewSet, basename='optimized_pca_model'
)


# OpenAPI generation
schema_view = get_schema_view(
    openapi.Info(title='ShapeWorks Cloud', default_version='v1', description=''),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', views.home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('admin/', admin.site.urls),
    path('api/v1/s3-upload/', include('s3_file_field.urls', namespace='s3ff')),
    path('api/v1/', include(router.urls)),
    path('api/docs/redoc/', schema_view.with_ui('redoc'), name='docs-redoc'),
    path('api/docs/swagger/', schema_view.with_ui('swagger'), name='docs-swagger'),
    path('api-token-auth/', obtain_auth_token),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
