"""
	This file contains all of the serializers that are shared
	between more than one apps.
"""
from rest_framework import serializers
from vpmotree.models import TreeStructure


class RelatedObjectIdField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return str(value)


class ObjectIdField(serializers.IntegerField):
    def to_representation(self, value):
        return str(value)

class MinimalNodeSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    name = serializers.CharField(max_length=150)
    node_type = serializers.CharField(max_length=120)
    model_name = serializers.CharField(max_length=48)

    # def get_name(self, instance):
    #     if instance._meta.model == TreeStructure:
    #         return instance.get_object().name
    #     return instance.name
