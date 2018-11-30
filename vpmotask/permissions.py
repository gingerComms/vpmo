from rest_framework import permissions
from django.apps import apps
from vpmotree.models import TreeStructure
from vpmotask.models import ScrumboardTaskList


class TaskPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            node = request.data["node"]
        else:
            node = request.query_params["nodeID"]

        node = TreeStructure.objects.get(_id=node)
        node = node.get_object()

        perms = request.user.get_permissions(node)

        if "update_{}".format(node.node_type.lower()) in perms:
            return True

        return False


class TaskListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            node = request.data["project_id"]
        elif request.method == "GET":
            node = view.kwargs["project_id"]
        else:
            node = request.query_params["project_id"]
        node = TreeStructure.objects.get(_id=node)
        node = node.get_object()

        perms = request.user.get_permissions(node)

        # If request is a GET, return for only view level perms, otherwise look for update perms
        if request.method == "GET":
            if "read_{}".format(node.node_type.lower()) in perms:
                return True
        else:
            if "update_{}".format(node.node_type.lower()) in perms:
                return True

        return False


class TaskReorderPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        node = ScrumboardTaskList.objects.get(_id=view.kwargs["task_list_id"]).project

        perms = request.user.get_permissions(node)

        # If request is a GET, return for only view level perms, otherwise look for update perms
        if request.method == "GET":
            if "read_{}".format(node.node_type.lower()) in perms:
                return True
        else:
            if "update_{}".format(node.node_type.lower()) in perms:
                return True

        return False


class ProjectTaskListPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        node = view.kwargs["project_id"]
        node = TreeStructure.objects.get(_id=node)
        node = node.get_object()

        perms = request.user.get_permissions(node)

        # If request is a GET, return for only view level perms, otherwise look for update perms
        if request.method == "GET":
            if "read_{}".format(node.node_type.lower()) in perms:
                return True
        else:
            if "update_{}".format(node.node_type.lower()) in perms:
                return True

        return False