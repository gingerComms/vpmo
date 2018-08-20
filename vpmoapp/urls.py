from django.conf.urls import url, include
from rest_framework import routers

from vpmoapp.views import *

# Imports related to Djangular API's
#  https://github.com/pyaf/djangular/blob/master/djangular/urls.py
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic import RedirectView
# End of API Imports

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = (
    url(r'^api/organisations$', AllTeamsView.as_view()),
    url(r'^api/filtered_organisations$', FilteredTeamsView.as_view(), name="filtered_teams"),
    url(r'^api/projects$', AllProjectsView.as_view()),
    url(r'^api/projects/add', CreateProjectView.as_view()),
    url(r'^api/teams/add', CreateTeamView.as_view()),

    url(r"^api/teams_tree/(?P<team_id>.+)/$", TeamTreeView.as_view(), name="team_tree_view"),

    url(r'^(?P<path>.*\..*)$', RedirectView.as_view(url='/static/%(path)s')),
    url(r'^', TemplateView.as_view(template_name='angular/index.html')),
)