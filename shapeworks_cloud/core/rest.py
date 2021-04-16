from typing import Dict, Type

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from . import filters, models, serializers, tasks


class Pagination(PageNumberPagination):
    page_size = 25
    max_page_size = 100
    page_size_query_param = 'page_size'


class BaseViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = Pagination

    serializer_class_dict: Dict[str, Type[BaseSerializer]] = {}
    serializer_class: Type[BaseSerializer]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        return self.serializer_class_dict.get(self.action, self.serializer_class)


class GroomedDatasetViewSet(BaseViewSet):
    queryset = models.GroomedDataset.objects.all().order_by('name')
    serializer_class = serializers.GroomedDatasetSerializer
    serializer_class_dict = {
        'create': serializers.CreateGroomedDatasetSerializer,
        'list': serializers.ListGroomedDatasetSerializer,
    }


class ProjectViewSet(BaseViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    serializer_class_dict = {
        'create': serializers.CreateProjectSerializer,
        'list': serializers.ListProjectSerializer,
    }


class OptimizationViewSet(BaseViewSet):
    queryset = models.Optimization.objects.all()
    serializer_class_dict = {
        'create': serializers.CreateOptimizationSerializer,
    }
    serializer_class = serializers.OptimizationSerializer
    filterset_class = filters.OptimizationFilter

    def create(self, request, **kwargs):
        params_serializer = serializers.CreateOptimizationSerializer(data=request.data)
        params_serializer.is_valid(raise_exception=True)

        project = params_serializer.validated_data.pop('project')
        optimization = models.Optimization.objects.create(project=project)
        models.OptimizationParameters.objects.create(
            optimization=optimization, **params_serializer.validated_data
        )

        tasks.optimize_shapes.delay(optimization.pk)

        optimization_serializer = serializers.OptimizationSerializer(optimization)
        return Response(optimization_serializer.data, status=status.HTTP_201_CREATED)
