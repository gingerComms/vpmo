from django.conf.urls import url, include
from rest_framework import routers

from vpmotree.views import *

# Imports related to Djangular API's
#  https://github.com/pyaf/djangular/blob/master/djangular/urls.py
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic import RedirectView
from django.urls import path
# End of API Imports

app_name = "vpmotree"

router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)

urlpatterns = (
    url(r'^api/organisations/$', AllTeamsView.as_view()),
    url(r'^api/projects/$', AllProjectsView.as_view(), name="all_projects"),
    url(r'^api/projects/add/$', CreateProjectView.as_view()),
    url(r'^api/teams/add/$', CreateTeamView.as_view(), name="create_team"),


    # Generic Views to create/update/retrieve any node that falls under the treestructure
    path("api/create_node/<str:nodeType>/", CreateNodeView.as_view(), name="create_node"),
    path("api/node/<str:nodeID>/", RetrieveUpdateNodeView.as_view(), name="node_retrieve_update"),

    # Takes two querys parametrs - nodeType + parentNodeID and returns all nodes under those based on permissions
    url(r'^api/nodes/$', AllNodesListView.as_view(), name="all_nodes"),

    # Takes node id and returns team and project (if applicable) as parents
    path(r'api/node_parents/<str:nodeID>/', NodeParentsListView.as_view(), name="node_parents"),
    

    url(r"^api/nodes_tree/(?P<nodeID>.+)/$", NodeTreeView.as_view(), name="node_tree_view"),

    url(r"^api/node_permissions/(?P<node_id>.+)/$", NodePermissionsView.as_view(), name="node_permissions"),
    url(r"^api/assignable_roles/(?P<node_id>.+)/$", AssignableRolesView.as_view(), name="assignable-roles"),

    url(r'^(?P<path>.*\..*)/$', RedirectView.as_view(url='/static/%(path)s')),
    url(r'^', TemplateView.as_view(template_name='angular/index.html')),
)