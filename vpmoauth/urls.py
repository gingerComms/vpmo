from django.conf.urls import url, include

from vpmoauth.views import *

from rest_framework_jwt.views import (obtain_jwt_token,
                                        verify_jwt_token,
                                        refresh_jwt_token)

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
    url(r'^api/users/(?P<id>\d+)/$', UserDetailsView.as_view()),
    url(r'^api/users/(?P<id>\d+)/update/$', UserUpdateView.as_view()),
    # User Permission Views
    url(r"^api/user_perms/$", UserPermissionsView.as_view(), name="user-perms"),
    url(r"^api/user_node_permissions/(?P<node_id>.+)/$", UserNodePermissionsView.as_view(), name="user-node-perms"),
    # Takes a user, role and node type as a GET query param (?user=<user._id>&node_type=<str>&role=<str>)
    url(r"^api/assign_role/(?P<node_id>.+)/", AssignRoleView.as_view(), name="assign-role")
]