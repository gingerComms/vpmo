from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import filters

from vpmoauth.models import MyUser

from vpmoapp.models import Team, Project
from vpmoapp.serializers import TeamSerializer, ProjectSerializer, TeamTreeSerializer
from vpmoapp.permissions import TeamPermissions
from vpmoapp.filters import TeamListFilter



class FilteredTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, TeamPermissions]
    queryset = Team.objects.all()
    filter_backends = (TeamListFilter,)


class AllProjectsView(ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()


class AllTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()


class CreateProjectView(CreateAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)


class CreateTeamView(CreateAPIView):
    model = Team
    serializer_class = TeamSerializer
    permission_classes = (IsAuthenticated,)


class TeamTreeView(RetrieveUpdateAPIView):
    model = Team
    serializer_class = TeamTreeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        try:
            team = Team.objects.get(_id=self.kwargs.get("id", None))
            return team
        except Team.DoesNotExist:
            return None
