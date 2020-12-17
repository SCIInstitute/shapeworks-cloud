from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet

from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel
from shapeworks_cloud.core.serializers import (
    DatasetSerializer,
    GroomedSerializer,
    ParticlesSerializer,
    SegmentationSerializer,
    ShapeModelSerializer,
)


class Pagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = 'page_size'


class DatasetViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = DatasetSerializer
    pagination_class = Pagination

    queryset = Dataset.objects.all()


class SegmentationViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = SegmentationSerializer
    pagination_class = Pagination

    queryset = Segmentation.objects.all()


class GroomedViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = GroomedSerializer
    pagination_class = Pagination

    queryset = Groomed.objects.all()


class ShapeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ShapeModelSerializer
    pagination_class = Pagination

    queryset = ShapeModel.objects.all()


class ParticlesViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ParticlesSerializer
    pagination_class = Pagination

    queryset = Particles.objects.all()
