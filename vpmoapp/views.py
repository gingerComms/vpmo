from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import filters

from vpmoauth.models import MyUser

from vpmoapp.models import Team, Project
from vpmoapp.serializers import TeamSerializer, ProjectSerializer
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



# class CreateUserView(CreateAPIView):
#     # CreateAPIView provide only Post method
#     model = get_user_model()
#     # set permission as AllowAny user to Register
#     permission_classes = (AllowAny,)
#     # queryset = get_user_model().object().all
#     serializer_class = UserSerializer


class CreateProjectView(CreateAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (AllowAny,)