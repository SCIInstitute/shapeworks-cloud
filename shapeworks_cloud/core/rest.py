from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_extensions.mixins import NestedViewSetMixin

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


class BaseViewSet(
    NestedViewSetMixin,
    DestroyModelMixin,
    UpdateModelMixin,
    ReadOnlyModelViewSet,
):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    # TODO this was the best way I could find to populate foreign keys.
    # Each ViewSet defines it's own create() which locates the parent entity, then delegates
    # to this method to handle the rest.
    def _create(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.model(**serializer.validated_data, **kwargs)
        instance.save()

        return Response({**{'id': instance.id}, **serializer.data}, status=201)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'filename',
                openapi.IN_QUERY,
                description='Search for a filename',
                type=openapi.TYPE_STRING,
            )
        ],
        request_body=no_body,
        responses={
            200: 'Search result list',
        },
    )
    @action(methods=['POST'], detail=False)
    def search(self, request, **kwargs):
        if 'filename' not in request.query_params:
            return Response([])
        filename = request.query_params['filename']
        objects = self.get_queryset().all()
        # Can't use queryset filtering because object.name is a computed property
        matching_objects = list(filter(lambda o: o.name == filename, objects))
        serializer: GroomedSerializer = self.get_serializer_class()(matching_objects, many=True)
        return Response(serializer.data)


class SegmentationViewSet(BaseViewSet):
    serializer_class = SegmentationSerializer
    model = Segmentation
    queryset = Segmentation.objects.all()

    def create(self, request, parent_lookup_dataset__pk):
        dataset = get_object_or_404(Dataset, pk=parent_lookup_dataset__pk)
        return self._create(request, dataset=dataset)


class GroomedViewSet(BaseViewSet):
    serializer_class = GroomedSerializer
    model = Groomed
    queryset = Groomed.objects.all()

    def create(self, request, parent_lookup_dataset__pk):
        dataset = get_object_or_404(Dataset, pk=parent_lookup_dataset__pk)
        return self._create(request, dataset=dataset)


class ShapeModelViewSet(BaseViewSet):
    serializer_class = ShapeModelSerializer
    model = ShapeModel
    queryset = ShapeModel.objects.all()

    def create(self, request, parent_lookup_dataset__pk):
        dataset = get_object_or_404(Dataset, pk=parent_lookup_dataset__pk)
        return self._create(request, dataset=dataset)


class ParticlesViewSet(BaseViewSet):
    serializer_class = ParticlesSerializer
    model = Particles
    queryset = Particles.objects.all()

    def create(
        self,
        request,
        parent_lookup_shape_model__dataset__pk,
        parent_lookup_shape_model__pk,
    ):
        shape_model = get_object_or_404(
            ShapeModel,
            pk=parent_lookup_shape_model__pk,
            dataset__pk=parent_lookup_shape_model__dataset__pk,
        )
        return self._create(request, shape_model=shape_model)
