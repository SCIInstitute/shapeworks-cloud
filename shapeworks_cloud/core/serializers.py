from rest_framework import serializers
from s3_file_field.rest_framework import S3FileSerializerField

from shapeworks_cloud.core import models


class CachedAnalysisModePCASerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CachedAnalysisModePCA
        fields = '__all__'


class CachedAnalysisModeSerializer(serializers.ModelSerializer):
    pca_values = CachedAnalysisModePCASerializer(many=True)

    class Meta:
        model = models.CachedAnalysisMode
        fields = '__all__'


class CachedAnalysisSerializer(serializers.ModelSerializer):
    modes = CachedAnalysisModeSerializer(many=True)

    class Meta:
        model = models.CachedAnalysis
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    file = S3FileSerializerField()
    last_cached_analysis = CachedAnalysisSerializer(allow_null=True)

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
    id = serializers.SerializerMethodField()
    file = S3FileSerializerField()
    pre_cropping = S3FileSerializerField(required=False, allow_null=True)
    pre_alignment = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.GroomedSegmentation
        fields = '__all__'

    def get_id(self, obj) -> int:
        return obj.segmentation_id


class GroomedMeshSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    file = S3FileSerializerField()
    pre_cropping = S3FileSerializerField(required=False, allow_null=True)
    pre_alignment = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.GroomedMesh
        fields = '__all__'

    def get_id(self, obj) -> int:
        return obj.mesh_id


class OptimizedShapeModelSerializer(serializers.ModelSerializer):
    parameters = serializers.DictField()

    class Meta:
        model = models.OptimizedShapeModel
        fields = '__all__'


class OptimizedParticlesSerializer(serializers.ModelSerializer):
    world = S3FileSerializerField()
    local = S3FileSerializerField()
    transform = S3FileSerializerField()
    constraints = S3FileSerializerField(required=False, allow_null=True)

    class Meta:
        model = models.OptimizedParticles
        fields = '__all__'


class OptimizedSurfaceReconstructionMetaSerializer(serializers.ModelSerializer):
    reconstruction_params = S3FileSerializerField()
    template_reconstruction = S3FileSerializerField()

    class Meta:
        model = models.OptimizedSurfaceReconstructionMeta
        fields = '__all__'


class OptimizedSurfaceReconstructionSerializer(serializers.ModelSerializer):
    sample_reconstruction = S3FileSerializerField()

    class Meta:
        model = models.OptimizedSurfaceReconstruction
        fields = '__all__'


class OptimizedPCAModelSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    mean_particles = S3FileSerializerField()
    pca_modes = S3FileSerializerField()
    eigen_spectrum = S3FileSerializerField()

    class Meta:
        model = models.OptimizedPCAModel
        fields = '__all__'

    def get_id(self, obj) -> int:
        return obj.shape_model.id
