from rest_framework import permissions
from vpmoauth.models import MyUser


class AssignRolesPermission(permissions.BasePermission):
    """ Permission that decides whether a user a can assign a permission or not """
    deliverable_types = ["Deliverable", "Topic"]

    def has_object_permission(self, request, view, obj):
        # Getting the role and permissions a user has for the object
        assigning_role = request.data.get("role")

        permissions = request.user.get_permissions(obj)

        if "update_{}_user_role".format(obj.node_type.lower()) in permissions:
            return True

        return False


class RemoveRolesPermission(permissions.BasePermission):
    """ Checks whether the requesting user has permissions to remove a user's role for a node """

    def has_object_permission(self, request, view, obj):
        permissions = request.user.get_permissions(obj)

        role = request.user.get_role(obj)
        if role == "team_admin":
            # Conditional that disallows a team-admin from deleting his own permission
            removing_user = request.query_params["user"]
            if removing_user == str(request.user._id):
                return False
            # Return False ALWAYS if the user is the team's owner (team created on register)
            if obj.node_type == "Team":
                if request.user.is_team_owner(obj):
                    return False

        if request.method == "DELETE" and "remove_{}_user".format(obj.node_type.lower()) in permissions:
            return True

        return False