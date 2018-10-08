from rest_framework import permissions
from guardian import shortcuts
from vpmoauth.models import MyUser


class AssignRolesPermission(permissions.BasePermission):
    """ Permission that decides whether a user a can assign a permission or not """
    deliverable_types = ["Deliverable", "Topic"]

    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)
        current_user_role = request.user.get_role(obj)
        if not perms and obj.node_type != "Team":
            parent = obj.get_parent()
            perms = shortcuts.get_user_perms(request.user, parent)
            current_user_role = request.user.get_role(parent)
        # Permission the user is trying to assign
        assigning_role = request.data.get("role")
        target_user = MyUser.objects.get(_id=request.data.get("userID"))
        # Only allowing PUT method for assigning permissions
        if request.method != "PUT":
            return False
        print(assigning_role, perms)
        # Team admin permission assignment
        if obj.node_type == "Team":
            if "edit_role" in perms:
                return True
        # Project permission assignment
        elif obj.node_type == "Project":
            if current_user_role == "team_admin":
                return True
                
            if assigning_role == "project_admin":
                required_perm = "assign_admin"
            elif assigning_role == "project_viewer":
                required_perm = "assign_viewer"
            else:
                required_perm = "assign_contributor"
            if required_perm in perms:
                return True
                    
        return False


class RemoveRolesPermission(permissions.BasePermission):
    """ Checks whether the requesting user has permissions to remove a user's role for a node """

    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)
        if not perms:
            perms = shortcuts.get_user_perms(request.user, obj.get_parent())

        if request.method == "DELETE" and "remove_user" in perms:
            return True

        return False