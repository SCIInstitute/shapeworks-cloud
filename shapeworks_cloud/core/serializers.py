from rest_framework import serializers

from shapeworks_cloud.core.models import Dataset, Groomed, Particles, Segmentation, ShapeModel


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = [
            'name',
            'created',
            'modified',
        ]
        read_only_fields = ['created']


class SegmentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segmentation
        fields = [
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
            'name',
            'blob',
            'created',
            'modified',
        ]
        read_only_fields = ['created']
