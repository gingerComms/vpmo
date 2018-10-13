from rest_framework import filters
from rest_framework import permissions
from guardian import shortcuts
from django.db.models import Q
from vpmotree.models import TreeStructure, Topic
from vpmoauth.models import UserRole


class TeamListFilter(filters.BaseFilterBackend):
    """ A custom DRF FilterBackend that filters out only objects that a user has permissions for
     FilterBackends are basically only effective for List Endpoints
    """

    def filter_queryset(self, request, queryset, view):
        # Return objects for ANY permissions if request method is in ["GET", "HEAD", "OPTIONS"]
        if request.method in permissions.SAFE_METHODS:
            return shortcuts.get_objects_for_user(user=request.user,
                                                perms=["created_obj", "contribute_obj", "read_obj"], klass=queryset,
                                                accept_global_perms=False, any_perm=True)
        # Return objects for contribute and owner permissions if request method is POST
        elif request.method in ["POST"]:
            return shortcuts.get_objects_for_user(user=request.user,
                                                perms=["created_obj", "contribute_obj"], klass=queryset,
                                                accept_global_perms=False, any_perm=True)
        # Return objects for only owner permissions if request method is not in above conditionals
        else:
            return shortcuts.get_objects_for_user(user=request.user,
                                                perms=["created_obj"], klass=queryset, accept_global_perms=False,
                                                any_perm=True)


class ReadNodeListFilter(filters.BaseFilterBackend):
    """ Filters the input queryset to only contain items that the user has at least read_obj permissions for
        NOTE: request must have nodeType and parentNodeID query parameters
    """

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params

        if request.method in permissions.SAFE_METHODS and "parentNodeID" in query_params and "nodeType" in query_params:
            parent_node = TreeStructure.objects.get(_id=query_params["parentNodeID"])
            nodes_in_parent_path = list(filter(lambda x: x.strip(), parent_node.path.split(",") if parent_node.path else []))
            # Adding the parent node itself into the array
            nodes_in_parent_path.append(str(parent_node._id))


            node_type = query_params["nodeType"]

            if node_type in Topic.topic_classes:
                node_type = "Topic"

            # Explanation:
            #   Q(node__id__in) | Q(node__path__endswith) -> filters nodes that are either above the parent or directly below it
            #   permissions__name__contains="read" -> filters the roles that have a read_<target_node_type> permission
            #   At the end, we're left with the nodes that have a direct assignment to the user + access to read_node_type
            assigned_nodes = UserRole.objects.filter(Q(node___id__in=nodes_in_parent_path) | Q(node__path__endswith=parent_node._id),
                permissions__name__icontains="read_{}".format(node_type), user=request.user).values_list(
                "node___id", flat=True)

            # Filtering for objects ending in parentNodeID (directly under the parent node)
            queryset = queryset.filter(path__endswith="{},".format(str(parent_node._id)))

            # Creating a condition of the node ID either being part of the directly assigned nodes
            condition = Q(_id__in=assigned_nodes)
            # Or having one of the assigned nodes in the path
            for node in assigned_nodes:
                condition |= Q(path__contains=node)

            # This makes the final query to the DB by filtering on the condition
            return queryset.filter(condition)

        return []
