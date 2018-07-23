from rest_framework import permissions
from guardian import shortcuts

class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.user:
            return account == request.user
        return False


class TeamPermissions(permissions.BasePermission):
	def has_permission(self, request, view):
		return True

	def has_object_permission(self, request, view, obj):
		return True
		print(request.user, obj)
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