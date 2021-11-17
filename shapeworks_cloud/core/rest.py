from typing import Dict, Type

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from . import filters, models, serializers


class Pagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = 'page_size'


class BaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    serializer_class_dict: Dict[str, Type[BaseSerializer]] = {}
    serializer_class: Type[BaseSerializer]

    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        return self.serializer_class_dict.get(self.action, self.serializer_class)


class DatasetViewSet(BaseViewSet):
    queryset = models.Dataset.objects.all().order_by('name')
    serializer_class = serializers.DatasetSerializer
    filterset_class = filters.DatasetFilter


class SubjectViewSet(BaseViewSet):
    queryset = models.Subject.objects.all().order_by('name')
    serializer_class = serializers.SubjectSerializer
    filterset_class = filters.SubjectFilter


class SegmentationViewSet(BaseViewSet):
    queryset = models.Segmentation.objects.all().order_by('subject')
    serializer_class = serializers.SegmentationSerializer
    filterset_class = filters.SegmentationFilter


class MeshViewSet(BaseViewSet):
    queryset = models.Mesh.objects.all().order_by('subject')
    serializer_class = serializers.MeshSerializer
    filterset_class = filters.MeshFilter


class ImageViewSet(BaseViewSet):
    queryset = models.Image.objects.all().order_by('subject')
    serializer_class = serializers.ImageSerializer
    filterset_class = filters.ImageFilter


class ProjectViewSet(BaseViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filterset_class = filters.ProjectFilter


class GroomedSegmentationViewSet(BaseViewSet):
    queryset = models.GroomedSegmentation.objects.all()
    serializer_class = serializers.GroomedSegmentationSerializer
    filterset_class = filters.GroomedSegmentationFilter


class GroomedMeshViewSet(BaseViewSet):
    queryset = models.GroomedMesh.objects.all()
    serializer_class = serializers.GroomedMeshSerializer
    filterset_class = filters.GroomedMeshFilter


class OptimizedShapeModelViewSet(BaseViewSet):
    queryset = models.OptimizedShapeModel.objects.all()
    serializer_class = serializers.OptimizedShapeModelSerializer
    filterset_class = filters.OptimizedShapeModelFilter


class OptimizedParticlesViewSet(BaseViewSet):
    queryset = models.OptimizedParticles.objects.all()
    serializer_class = serializers.OptimizedParticlesSerializer
    filterset_class = filters.OptimizedShapeModelFilter


class OptimizedSurfaceReconstructionMetaViewSet(BaseViewSet):
    queryset = models.OptimizedSurfaceReconstructionMeta.objects.all()
    serializer_class = serializers.OptimizedSurfaceReconstructionMetaSerializer


class OptimizedSurfaceReconstructionViewSet(BaseViewSet):
    queryset = models.OptimizedSurfaceReconstruction.objects.all()
    serializer_class = serializers.OptimizedSurfaceReconstructionSerializer


class OptimizedPCAModelViewSet(BaseViewSet):
    queryset = models.OptimizedPCAModel.objects.all()
    serializer_class = serializers.OptimizedPCSModelSerializer
    filterset_class = filters.OptimizedPCAModelFilter
