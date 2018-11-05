from rest_framework import serializers

from vpmodoc.models import *
from vpmotree.serializers import RelatedObjectIdField, ObjectIdField


class NodeDocumentSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    node = RelatedObjectIdField(queryset=TreeStructure.objects.all())
    uploaded_by = serializers.SerializerMethodField()

    # Document related fields
    document_name = serializers.SerializerMethodField()
    document_size = serializers.SerializerMethodField()

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

    def get_uploaded_by(self, instance):
        return instance.uploaded_by.username

    class Meta:
        model = NodeDocument
        fields = ["_id", "node", "uploaded_at", "uploaded_by", "document", "document_name", "document_size"]