from rest_framework import serializers
from s3_file_field.rest_framework import S3FileSerializerField

from shapeworks_cloud.core import models


class LandmarksSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField(required=False)

    class Meta:
        model = models.Landmarks
        fields = '__all__'


class CachedAnalysisGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysisGroup
        fields = '__all__'


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
    file = S3FileSerializerField(required=False)

    class Meta:
        model = models.Project
        fields = '__all__'


class CachedAnalysisGroupReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysisGroup
        fields = '__all__'


class CachedAnalysisModeReadSerializer(serializers.ModelSerializer):
    pca_values = CachedAnalysisModePCASerializer(many=True)

    class Meta:
        model = models.CachedAnalysisMode
        fields = '__all__'


class CachedAnalysisReadSerializer(serializers.ModelSerializer):
    modes = CachedAnalysisModeReadSerializer(many=True)
    groups = CachedAnalysisGroupReadSerializer(many=True)

    class Meta:
        model = models.CachedAnalysis
        fields = '__all__'


class ProjectReadSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    last_cached_analysis = CachedAnalysisReadSerializer(allow_null=True)
    landmarks = LandmarksSerializer(many=True)

    class Meta:
        model = models.Project
        fields = '__all__'


class ProjectDownloadSerializer(serializers.ModelSerializer):
    download_paths = serializers.SerializerMethodField('get_download_paths')

    def get_download_paths(self, obj):
        return obj.get_download_paths()

    class Meta:
        model = models.Project
        fields = ['download_paths', 'id']


class DatasetSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(required=False, many=True)
    summary = serializers.SerializerMethodField('get_summary')
    creator = serializers.SerializerMethodField('get_creator')

    def get_creator(self, obj):
        if obj.creator:
            return obj.creator.username
        return ''

    def get_summary(self, obj):
        summary = ''
        meshes = models.Mesh.objects.filter(subject__dataset=obj)
        segmentations = models.Segmentation.objects.filter(subject__dataset=obj)
        meshes_count = meshes.count()
        segmentations_count = segmentations.count()
        if meshes_count > 0:
            summary += f'{meshes_count} meshes'
        if meshes_count > 0 and segmentations_count > 0:
            summary += ', '
        if segmentations_count > 0:
            summary += f'{segmentations_count} segmentations'
        return summary

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


class ContourSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Contour
        fields = '__all__'


class ImageSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Image
        fields = '__all__'


class ConstraintsSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()

    class Meta:
        model = models.Constraints
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
    world = S3FileSerializerField(required=False, allow_null=True)
    local = S3FileSerializerField(required=False, allow_null=True)
    transform = S3FileSerializerField(required=False, allow_null=True)
    constraints = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.OptimizedParticles
        fields = '__all__'


class OptimizedParticlesReadSerializer(OptimizedParticlesSerializer):
    groomed_mesh = GroomedMeshSerializer(required=False, allow_null=True)
    groomed_segmentation = GroomedSegmentationSerializer(required=False, allow_null=True)


class ReconstructedSampleSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    particles = OptimizedParticlesReadSerializer(required=False)

    class Meta:
        model = models.ReconstructedSample
        fields = '__all__'


class TaskProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TaskProgress
        fields = '__all__'
