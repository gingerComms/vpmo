from django.conf.urls import url, include

from vpmoauth.views import *

from rest_framework_jwt.views import (obtain_jwt_token,
                                        verify_jwt_token,
                                        refresh_jwt_token)

app_name = "vpmoauth"


urlpatterns = [
	url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
	# JWT Views
    url(r'^api/auth/token/$', obtain_jwt_token),
    url(r'^api/token-refresh/$', refresh_jwt_token),
    url(r'^api/token-verify/$', verify_jwt_token),
    # Generic User Views
    url(r'^api/users$', AllUserView.as_view()),
    url(r'^api/users/register/$', CreateUserView.as_view(), name='user'),
    url(r'^api/users/login/$', LoginUserView.as_view()),
    url(r'^api/users/update/(?P<_id>.+)/$', UserUpdateView.as_view()),
    url(r'^api/users/(?P<_id>.+)$', UserDetailsView.as_view()),
    # User Permission Views
    url(r"^api/user_node_permissions/(?P<node_id>.+)/$", UserNodePermissionsView.as_view(), name="user-node-perms"),
    url(r"^api/remove_user_role/(?P<node_id>.+)/$", RemoveUserRoleView.as_view(), name="remove-user-role"),
    # Takes a user, role and node type as a GET query param (?user=<user._id>&node_type=<str>&role=<str>)
    url(r"^api/assignable_users/(?P<node_id>.+)/$", AssignableUsersListView.as_view(), name="assignable-users-list"),
    url(r"^api/assign_role/$", AssignRoleView.as_view(), name="assign-role"),

    url(r"^api/favorite_nodes/", FavoriteNodesView.as_view(), name="favorite-nodes")
]