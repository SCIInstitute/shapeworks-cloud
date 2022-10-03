from typing import Dict, Type

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from . import filters, models, serializers
from .tasks import groom, optimize


class Pagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = 'page_size'


class BaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
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
    filterset_class = filters.ProjectFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.ProjectReadSerializer
        else:
            return serializers.ProjectSerializer

    def create(self, request, **kwargs):
        data = request.data
        data['dataset'] = models.Dataset.objects.get(id=data['dataset'])
        project = models.Project.objects.create(**data)
        project.create_new_file()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path='groom',
        url_name='groom',
        methods=['POST'],
    )
    def groom(self, request, **kwargs):
        project = self.get_object()
        form_data = request.data
        groom.delay(request.user.id, project.id, form_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path='optimize',
        url_name='optimize',
        methods=['POST'],
    )
    def optimize(self, request, **kwargs):
        project = self.get_object()
        form_data = request.data
        optimize.delay(request.user.id, project.id, form_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroomedSegmentationViewSet(BaseViewSet):
    queryset = models.GroomedSegmentation.objects.all()
    serializer_class = serializers.GroomedSegmentationSerializer
    filterset_class = filters.GroomedSegmentationFilter


class GroomedMeshViewSet(BaseViewSet):
    queryset = models.GroomedMesh.objects.all()
    serializer_class = serializers.GroomedMeshSerializer
    filterset_class = filters.GroomedMeshFilter


class OptimizedParticlesViewSet(BaseViewSet):
    queryset = models.OptimizedParticles.objects.all()
    serializer_class = serializers.OptimizedParticlesSerializer
    filterset_class = filters.OptimizedParticlesFilter


class CachedAnalysisViewSet(BaseViewSet):
    queryset = models.CachedAnalysis.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.CachedAnalysisReadSerializer
        else:
            return serializers.CachedAnalysisSerializer


class CachedAnalysisModeViewSet(BaseViewSet):
    queryset = models.CachedAnalysisMode.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return serializers.CachedAnalysisModeReadSerializer
        else:
            return serializers.CachedAnalysisModeSerializer


class CachedAnalysisModePCAViewSet(BaseViewSet):
    queryset = models.CachedAnalysisModePCA.objects.all()
    serializer_class = serializers.CachedAnalysisModePCASerializer
