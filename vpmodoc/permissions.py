from rest_framework import permissions
from django.apps import apps
from vpmotree.models import TreeStructure
from vpmotask.models import Task


class IsAdminOrContributor(permissions.BasePermission):
    """ Permissions that checks that the user is at least a admin/contributor """
    def has_permission(self, request, view):
        node_type = request.query_params["nodeType"]
        node = view.kwargs["nodeID"]

        # TODO - Add conditional that asserts that node_type is either Project or Topic

        node = TreeStructure.objects.get(_id=node)

        perms = request.user.get_permissions(node)

        try:
            if "update_{}".format(node_type.lower()) in perms:
                return True
        except:
            print(perms, node_type)

        return False


class HasTaskUpdatePermission(permissions.BasePermission):
    """ Permission that checks that the user has at least update level 
        permissions against the given task's node
    """
    def has_permission(self, request, view):
        task = Task.objects.get(_id=view.kwargs["taskID"])

        node = task.node

        perms = request.user.get_permissions(node)

        try:
            if "update_{}".format(node.node_type.lower()) in perms:
                return True
        except:
            print(perms, node.node_type)

        return False
