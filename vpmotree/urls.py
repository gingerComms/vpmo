from django.conf.urls import url, include
from rest_framework import routers

from vpmotree.views import *

# Imports related to Djangular API's
#  https://github.com/pyaf/djangular/blob/master/djangular/urls.py
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic import RedirectView
# End of API Imports

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = (
    url(r'^api/organisations/$', AllTeamsView.as_view()),
    url(r'^api/filtered_organisations/$', FilteredTeamsView.as_view(), name="filtered_teams"),
    url(r'^api/projects/$', AllProjectsView.as_view(), name="all_projects"),
    url(r'^api/projects/add/$', CreateProjectView.as_view()),
    url(r'^api/projects/(?P<Project_id>.+)/$', UpdateProjectView.as_view()),
    url(r'^api/teams/add/$', CreateTeamView.as_view()),
    url(r'^api/deliverable/add/$', CreateDeliverableView.as_view()),
    # Takes two querys parametrs - nodeType + parentNodeID and returns all nodes under those based on permissions
    url(r'^api/nodes/$', AllNodesView.as_view(), name="all_nodes"),

    url(r"^api/update_project/(?P<_id>.+)/$", UpdateProjectView.as_view(), name="update_project"),

    url(r"^api/teams_tree/(?P<team_id>.+)/$", TeamTreeView.as_view(), name="team_tree_view"),
    url(r"^api/project_tree/(?P<project_id>.+)/$", ProjectTreeView.as_view(), name="project_tree_view"),

    url(r'^api/messages/(?P<node_id>.+)/$', MessageListView.as_view(), name="message_list"),

    url(r"^api/node_permissions/(?P<node_id>.+)/$", NodePermissionsView.as_view(), name="node_permissions"),
    url(r"^api/assignable_roles/(?P<node_id>.+)/$", AssignableRolesView.as_view(), name="assignable-roles"),

    url(r'^(?P<path>.*\..*)/$', RedirectView.as_view(url='/static/%(path)s')),
    url(r'^', TemplateView.as_view(template_name='angular/index.html')),
)