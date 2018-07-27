from django.conf.urls import url, include
from rest_framework import routers

from .api import (AllTeamsView, AllUserView, AllProjectsView, CreateUserView,
                  LoginUserView, CreateProjectView, UserUpdateView, UserDetailsView,
                  UserPermissionsView)



# Imports related to Djangular API's
#  https://github.com/pyaf/djangular/blob/master/djangular/urls.py
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic import RedirectView
from rest_framework_jwt.views import (obtain_jwt_token,
                                        verify_jwt_token,
                                        refresh_jwt_token)
# End of API Imports

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = (
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^api/auth/token/', obtain_jwt_token),
    url(r'^api/token-refresh', refresh_jwt_token),
    url(r'^api/token-verify', verify_jwt_token),
    url(r'^api/users$', AllUserView.as_view()),
    url(r'^api/users/register', CreateUserView.as_view(), name='user'),
    url(r'^api/users/login', LoginUserView.as_view()),
    url(r'^api/users/(?P<id>\d+)/$', UserDetailsView.as_view()),
    url(r'^api/users/(?P<id>\d+)/update$', UserUpdateView.as_view()),
    url(r'^api/organisations$', AllTeamsView.as_view()),
    url(r'^api/projects$', AllProjectsView.as_view()),
    url(r'^api/projects/add', CreateProjectView.as_view()),

    url(r"^api/user_perms/$", UserPermissionsView.as_view()),

    url(r'^(?P<path>.*\..*)$', RedirectView.as_view(url='/static/%(path)s')),
    url(r'^', TemplateView.as_view(template_name='angular/index.html')),
)