from rest_framework import permissions
from django.apps import apps
from vpmotree.models import TreeStructure


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.user:
            return account == request.user
        return False


class ReadPermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least read permissions using a Safe Method """
    def has_object_permission(self, request, view, obj):
        perms = request.user.get_permissions(obj)

        if "read_{}".format(obj.node_type) in perms in request.method in permissions.SAFE_METHODS:
            return True
        return False


class UpdatePermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least Update permissions on an object
        for a PUT/PATCH request
    """
    def has_object_permission(self, request, view, obj):
        perms = request.user.get_permissions(obj)

        if "update_{}".format(obj.node_type) in perms and request.method in ["PUT", "PATCH"]:
            return True
        return False


class DeletePermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least delete perms on an object
        for DELETE requests
    """
    def has_object_permission(self, request, view, obj):
        perms = request.user.get_permissions(obj)

        if "delete_{}".format(obj.node_type) in perms and request.method == "DELETE":
            return True
        return False


class CreatePermissions(permissions.BasePermission):
    """ Returns True for an object if the user has at least create perms on an object
        for POST requests
    """
    def has_permission(self, request, view):
        """ Assuming that the request has a parent attribute for the node to create """
        if request.method == "POST":
            node = request.data.get("parent")
            node = TreeStructure.objects.get(_id=node)
            perms = request.user.get_permissions(node, all_types=True)

            to_create_type = request.data["node_type"]
            if "create_{}".format(to_create_type.lower()) in perms:
                return True
        return False

    def has_object_permissions(self, request, view, obj):
        perms = request.user.get_permissions(obj)
        if "create_{}".format(obj.node_type) in perms and request.method == "POST":
            return True
        return False


class TeamPermissions(permissions.BasePermission):
    """ Custom DRF Permissions that returns True or False based on
        the permissions a user has for a given object.
    """

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        """ This method only comes into effect for a Detail Endpoint """
        # Retrieving all permissions a user has for the object
        perms = request.user.get_permissions(obj)

        if request.method in permissions.SAFE_METHODS:
            # Checking if the user has ANY perms for the obj and returns True
            if "read_{}".format(obj.node_type) in perms:
                return True
            return False
        else:
            # Checking if the user has creator or contributor perms for other methods
            if "created_{}".format(obj.node_type) in perms or "update_{}".format(obj.node_type) in perms:
                return True
            return False
        return False


class TaskListCreateAssignPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        node = request.query_params["nodeID"]
        node = TreeStructure.objects.get(_id=node)
        node = node.get_object()

        perms = request.user.get_permissions(node)

        if "update_{}".format(node.node_type.lower()) in perms:
            return True

        return False