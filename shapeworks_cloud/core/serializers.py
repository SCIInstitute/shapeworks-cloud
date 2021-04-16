from rest_framework import serializers
from s3_file_field.rest_framework import S3FileSerializerField

from shapeworks_cloud.core import models


# This class is only used internally for nested validation.  We don't
# expose these models directly through the API.
class _CreateGroomedSegmentationSerializer(serializers.ModelSerializer):
    blob = S3FileSerializerField()

    class Meta:
        model = models.GroomedSegmentation
        fields = ['name', 'blob']


class CreateGroomedDatasetSerializer(serializers.ModelSerializer):
    segmentations = _CreateGroomedSegmentationSerializer(many=True)

    class Meta:
        model = models.GroomedDataset
        read_only_fields = ['id', 'created', 'num_segmentations']
        fields = ['id', 'created', 'modified', 'name', 'num_segmentations', 'segmentations']

    def create(self, validated_data):
        segmentations = validated_data.pop('segmentations')
        dataset = models.GroomedDataset.objects.create(**validated_data)
        for index, segmentation in enumerate(segmentations):
            models.GroomedSegmentation.objects.create(
                dataset=dataset,
                index=index,
                **segmentation,
            )
        return dataset


class GroomedSegmentationSerializer(serializers.ModelSerializer):
    blob = serializers.SerializerMethodField()
    mesh = serializers.SerializerMethodField()

    class Meta:
        model = models.GroomedSegmentation
        fields = ['blob', 'mesh']

    def get_blob(self, obj):
        return obj.blob.url

    def get_mesh(self, obj):
        return obj.mesh.url


class ListGroomedDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GroomedDataset
        fields = ['id', 'created', 'modified', 'name', 'num_segmentations']


class GroomedDatasetSerializer(serializers.ModelSerializer):
    segmentations = GroomedSegmentationSerializer(many=True, read_only=True)

    class Meta:
        model = models.GroomedDataset
        fields = ['created', 'modified', 'name', 'segmentations']
        read_only_fields = ['created']

        # https://github.com/axnsan12/drf-yasg/issues/239#issuecomment-442629230
        ref_name = None  # type: ignore


class ShapeModelSerializer(serializers.ModelSerializer):
    local = serializers.SerializerMethodField()
    world = serializers.SerializerMethodField()

    class Meta:
        model = models.ShapeModel
        fields = ['local', 'world']
        # https://github.com/axnsan12/drf-yasg/issues/239#issuecomment-442629230
        ref_name = None  # type: ignore

    def get_local(self, obj):
        return obj.local.url

    def get_world(self, obj):
        return obj.world.url


class OptimizationParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OptimizationParameters
        exclude = ['optimization']

        # https://github.com/axnsan12/drf-yasg/issues/239#issuecomment-442629230
        ref_name = None  # type: ignore


class OptimizationCheckpointSerializer(serializers.ModelSerializer):
    shape_model = ShapeModelSerializer(read_only=True)

    class Meta:
        model = models.OptimizationCheckpoint
        fields = ['split', 'iteration', 'number_of_particles']


class CreateOptimizationSerializer(OptimizationParametersSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=models.Project.objects.all())


class OptimizationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(read_only=True)  # type: ignore
    queued = serializers.BooleanField(read_only=True)
    finished = serializers.BooleanField(read_only=True)
    parameters = OptimizationParametersSerializer(read_only=True)

    shape_model = ShapeModelSerializer(read_only=True)

    class Meta:
        model = models.Optimization
        read_only_fields = [
            'id',
            'created',
            'running',
            'queued',
            'finished',
            'error',
            'shapeworks_version',
        ]
        fields = [
            'id',
            'created',
            'modified',
            'shapeworks_version',
            'shape_model',
            'error',
            'running',
            'queued',
            'finished',
            'parameters',
            'project',
        ]


class CreateProjectSerializer(serializers.ModelSerializer):
    groomed_dataset = serializers.PrimaryKeyRelatedField(
        queryset=models.GroomedDataset.objects.all()
    )

    class Meta:
        model = models.Project
        fields = '__all__'
        read_only_fields = ['created']


class ListProjectSerializer(serializers.ModelSerializer):
    groomed_dataset = ListGroomedDatasetSerializer()

    class Meta:
        model = models.Project
        read_only_fields = ['created']
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    groomed_dataset = GroomedDatasetSerializer(read_only=True)

    class Meta:
        model = models.Project
        read_only_fields = ['created']
        fields = '__all__'
