from rest_framework import permissions
from django.apps import apps
from vpmotree.models import TreeStructure


class TaskListCreateAssignPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        node = request.query_params["nodeID"]
        node = TreeStructure.objects.get(_id=node)
        node = node.get_object()

        perms = request.user.get_permissions(node)

        if "update_{}".format(node.node_type.lower()) in perms:
            return True

        return False