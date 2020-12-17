from rest_framework import serializers

from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'id',
            'name',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class SegmentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segmentation
        fields = [
            'id',
            'name',
            'blob',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class GroomedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Groomed
        fields = [
            'id',
            'name',
            'blob',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class ShapeModelSerializer(serializers.ModelSerializer):
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


class ParticlesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Particles
        fields = [
            'id',
            'name',
            'blob',
            'created',
            'modified',
        ]
        read_only_fields = ['created']
