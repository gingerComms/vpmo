from rest_framework import permissions
from guardian import shortcuts


class AssignRolesPermission(permissions.BasePermission):
    """ Permission that decides whether a user a can assign a permission or not """
    deliverable_types = ["Deliverable", "Topic"]

    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)
        # Permission the user is trying to assign
        assigning_role = request.query_params.get("role")
        target_user = MyUser.objects.get(_id=request.query_params.get("user"))
        # Only allowing PUT method for assigning permissions
        if request.method != "PUT":
            return False

        # Team admin permission assignment
        if obj.node_type == "Team":
            if "create_obj" in perms and "delete_obj" in perms:
                return True
        # Project permission assignment
        elif obj.node_type == "Project":
            if assigning_role == "project_admin":
                existing_admins = obj.get_users_with_role("project_admin")
                if request.user in existing_admins:
                    return True
            else:
                existing_contributors = obj.get_users_with_role("project_contributor")
                if request.user in existing_contributors:
                    return True
                    
        return False