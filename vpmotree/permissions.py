from rest_framework import permissions
from guardian import shortcuts


class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.user:
            return account == request.user
        return False


class AssignPermissionsPermission(permission.BasePermission):
    """ Permission that decides whether a user a can assign a permission or not """
    deliverable_types = ["Deliverable", "Topic"]

    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)
        # Permission the user is trying to assign
        assigning_perm = request.query_params.get("perm")
        # Only allowing PUT method for assigning permissions
        if request.method != "PUT":
            return False

        # Team admin permission assignment
        if obj.node_type == "Team":
            if "create_obj" in perms and "delete_obj" in perms:
                return True
        # This is enough to handle both Projects and Topics
        else:
            if "read_obj" in perms and "update_obj" in perms:
                return True

        return False


class ReadPermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least read permissions using a Safe Method """
    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)

        if "read_obj" in perms in request.method in permissions.SAFE_METHODS:
            return True
        return False


class UpdatePermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least Update permissions on an object
        for a PUT/PATCH request
    """
    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)

        if "update_obj" in perms and request.method in ["PUT", "PATCH"]:
            return True
        return False


class DeletePermission(permissions.BasePermission):
    """ Returns True for an object if the user has at least delete perms on an object
        for DELETE requests
    """
    def has_object_permission(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)

        if "delete_obj" in perms and request.method == "DELETE":
            return True
        return False


class CreatePermissions(permissions.BasePermission):
    """ Returns True for an object if the user has at least create perms on an object
        for POST requests
    """
    def has_object_permissions(self, request, view, obj):
        perms = shortcuts.get_user_perms(request.user, obj)

        if "create_obj" in perms and request.method == "POST":
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
        perms = shortcuts.get_user_perms(request.user, obj)

        if request.method in permissions.SAFE_METHODS:
            # Checking if the user has ANY perms for the obj and returns True
            if perms:
                return True
            return False
        else:
            # Checking if the user has creator or contributor perms for other methods
            if "created_obj" in perms or "contribute_obj" in perms:
                return True
            return False
        return False

