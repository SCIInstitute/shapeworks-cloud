from rest_framework import serializers

from shapeworks_cloud.core.metadata import METADATA_FIELDS
from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'groomed_pattern',
            'segmentation_pattern',
            'particles_pattern',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class BlobModelSerializer(serializers.ModelSerializer):
    # The default blob field is readonly, but we need it to be required for model creation
    blob = serializers.CharField()

    class Meta:
        abstract = True
        fields = [
            'id',
            'name',
            'blob',
            'created',
            'modified',
        ] + METADATA_FIELDS
        read_only_fields = ['created']


class SegmentationSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Segmentation


class GroomedSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Groomed


class ShapeModelSerializer(serializers.ModelSerializer):
    # The default S3FFs are readonly, but we need them to be required for model creation
    analyze = serializers.CharField()
    correspondence = serializers.CharField()
    transform = serializers.CharField()

    class Meta:
        model = ShapeModel
        fields = [
            'id',
            'name',
            'analyze',
            'correspondence',
            'transform',
            'magic_number',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class ParticlesSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Particles
