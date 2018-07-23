from rest_framework import filters
from rest_framework import permissions
from guardian import shortcuts


class TeamListFilter(filters.BaseFilterBackend):
	def filter_queryset(self, request, queryset, view):
		if request.method in permissions.SAFE_METHODS:
			return shortcuts.get_objects_for_user(user=request.user,
				perms=["created_obj", "contribut_obj", "read_obj"], klass=queryset,
				accept_global_perms=False, any_perm=True)
		elif request.method in ["POST"]:
			return shortcuts.get_objects_for_user(user=request.user,
				perms=["created_obj", "contribut_obj"], klass=queryset,
				accept_global_perms=False, any_perm=True)
		else:
			return shortcuts.get_objects_for_user(user=request.user,
				perms=["created_obj"], klass=queryset, accept_global_perms=False,
				any_perm=True)