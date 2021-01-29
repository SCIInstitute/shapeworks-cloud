from django.core import signing
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
            'num_groomed',
            'num_segmentations',
            'num_shape_models',
            'size',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class BlobModelSerializer(serializers.ModelSerializer):
    blob = serializers.FileField(read_only=True)
    field_value = serializers.CharField(write_only=True)

    class Meta:
        abstract = True
        fields = [
            'id',
            'name',
            'blob',
            'field_value',
            'created',
            'modified',
        ] + METADATA_FIELDS
        extra_kwargs = {'blob': {'read_only': False}}
        read_only_fields = ['created']

    def validate(self, data):
        # Extract the object_key from field_value and set blob to that
        data['blob'] = signing.loads(data['field_value'])['object_key']
        # Remove field_value
        data.pop('field_value')
        return data


class SegmentationSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Segmentation


class GroomedSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Groomed


class ShapeModelSerializer(serializers.ModelSerializer):
    analyze = serializers.FileField(read_only=True)
    correspondence = serializers.FileField(read_only=True)
    transform = serializers.FileField(read_only=True)
    analyze_field_value = serializers.CharField(write_only=True)
    correspondence_field_value = serializers.CharField(write_only=True)
    transform_field_value = serializers.CharField(write_only=True)

    class Meta:
        model = ShapeModel
        fields = [
            'id',
            'name',
            'analyze',
            'correspondence',
            'transform',
            'analyze_field_value',
            'correspondence_field_value',
            'transform_field_value',
            'magic_number',
            'num_particles',
            'size',
            'created',
            'modified',
        ]
        read_only_fields = ['created']

    def validate(self, data):
        # Extract the object_keys from the field_values and set the blobs to that
        data['analyze'] = signing.loads(data['analyze_field_value'])['object_key']
        data['correspondence'] = signing.loads(data['correspondence_field_value'])['object_key']
        data['transform'] = signing.loads(data['transform_field_value'])['object_key']
        # Remove the field_values
        data.pop('analyze_field_value')
        data.pop('correspondence_field_value')
        data.pop('transform_field_value')
        return data


class ParticlesSerializer(BlobModelSerializer):
    class Meta(BlobModelSerializer.Meta):
        model = Particles
