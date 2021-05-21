from rest_framework import serializers
from s3_file_field.rest_framework import S3FileSerializerField

from shapeworks_cloud.core import models


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dataset
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Subject
        fields = '__all__'


class SegmentationSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Segmentation
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Project
        fields = '__all__'


class GroomedSegmentationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    file = S3FileSerializerField()
    pre_cropping = S3FileSerializerField(required=False, allow_null=True)
    pre_alignment = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.GroomedSegmentation
        fields = '__all__'

    def get_id(self, obj) -> int:
        return obj.segmentation_id


class OptimizedShapeModelSerializer(serializers.ModelSerializer):
    parameters = serializers.DictField()

    class Meta:
        model = models.OptimizedShapeModel
        fields = '__all__'


class OptimizedParticlesSerializer(serializers.ModelSerializer):
    world = S3FileSerializerField()
    local = S3FileSerializerField()
    transform = S3FileSerializerField()

    class Meta:
        model = models.OptimizedParticles
        fields = '__all__'
