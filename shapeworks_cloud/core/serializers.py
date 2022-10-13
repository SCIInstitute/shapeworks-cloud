from rest_framework import serializers
from s3_file_field.rest_framework import S3FileSerializerField

from shapeworks_cloud.core import models


class CachedAnalysisModePCASerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysisModePCA
        fields = '__all__'


class CachedAnalysisModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysisMode
        fields = '__all__'


class CachedAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysis
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Project
        fields = '__all__'


class CachedAnalysisModeReadSerializer(serializers.ModelSerializer):
    pca_values = CachedAnalysisModePCASerializer(many=True)

    class Meta:
        model = models.CachedAnalysisMode
        fields = '__all__'


class CachedAnalysisReadSerializer(serializers.ModelSerializer):
    modes = CachedAnalysisModeReadSerializer(many=True)

    class Meta:
        model = models.CachedAnalysis
        fields = '__all__'


class ProjectReadSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    last_cached_analysis = CachedAnalysisReadSerializer(allow_null=True)

    class Meta:
        model = models.Project
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField(required=False, allow_null=True)
    projects = ProjectSerializer(required=False, many=True)

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


class MeshSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Mesh
        fields = '__all__'


class ImageSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Image
        fields = '__all__'


class GroomedSegmentationSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    pre_cropping = S3FileSerializerField(required=False, allow_null=True)
    pre_alignment = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.GroomedSegmentation
        fields = '__all__'


class GroomedMeshSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    pre_cropping = S3FileSerializerField(required=False, allow_null=True)
    pre_alignment = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.GroomedMesh
        fields = '__all__'


class OptimizedParticlesSerializer(serializers.ModelSerializer):
    world = S3FileSerializerField()
    local = S3FileSerializerField()
    transform = S3FileSerializerField()
    constraints = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.OptimizedParticles
        fields = '__all__'
