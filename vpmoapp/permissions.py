from rest_framework import permissions
from guardian import shortcuts

class IsAccountOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, account):
        if request.user:
            return account == request.user
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