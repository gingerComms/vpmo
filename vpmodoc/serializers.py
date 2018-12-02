from rest_framework import serializers

from vpmodoc.models import *
from vpmotask.models import Task
from vpmotree.serializers import RelatedObjectIdField
from vpmoprj.serializers import ObjectIdField, RelatedObjectIdField


class BaseDocumentSerializer(serializers.Serializer):
    """ A Base serializer that implements all of the document related fields """
    uploaded_by = serializers.SerializerMethodField()

    # Document related fields
    document_name = serializers.SerializerMethodField()
    document_size = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    def get_document_name(self, instance):
        try:
            return instance.document.name.replace("{}/".format(str(instance.node._id)), "")
        except ValueError:
            return None

    def get_document_size(self, instance):
        try:
            return instance.document.size
        except ValueError:
            return None

    def get_document_url(self, instance):
        try:
            return instance.document.url
        except ValueError:
            return None

    def get_uploaded_by(self, instance):
        return instance.uploaded_by.username


class NodeDocumentSerializer(BaseDocumentSerializer, serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    node = RelatedObjectIdField(queryset=TreeStructure.objects.all())

    class Meta:
        model = NodeDocument
        fields = ["_id", "node", "uploaded_at", "uploaded_by", "document", "document_name", "document_size", "document_url"]


class TaskDocumentSerializer(BaseDocumentSerializer, serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    task = RelatedObjectIdField(queryset=Task.objects.all())

    class Meta:
        model = TaskDocument
        fields = ["_id", "task", "uploaded_at", "uploaded_by", "document", "document_name", "document_size", "document_url"]


class TaskDocumentMinimalSerializer(BaseDocumentSerializer, serializers.ModelSerializer):
    """ A minimal serializer containing only the url, _id and name of a Document """
    _id = ObjectIdField(read_only=True)

    # Turning off unrequired fields from the base serializer
    task = None
    uploaded_by = None
    document_size=None

    class Meta:
        model = TaskDocument
        fields = ["_id", "document_name", "document_url", "uploaded_at"]
