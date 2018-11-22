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

class MinimalNodeSerialiizer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    name = serializers.SerializerMethodField()
    node_type = serializers.CharField(max_length=120)

    def get_name(self, instance):
        if instance._meta.model == TreeStructure:
            return instance.get_object().name
        return instance.name
