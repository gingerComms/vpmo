from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import filters
from rest_framework import status

from vpmoauth.models import MyUser

from vpmoapp.models import *
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

    topics = {
        "Deliverable": Deliverable
    }

    def get_object(self):
        """ Returns the team obuject from the url id arg """
        try:
            team = Team.objects.get(_id=self.kwargs.get("team_id", None))
            return team
        except Team.DoesNotExist:
            return None

    def handle_children(self, child, last_model=None, index=0):
        class_name = child["obj_type"]
        next_children = child.get("children", [])

        if class_name == "Project":
            project = Project.objects.get(_id=child["_id"])

            # Set project's parent to last model
            if isinstance(last_model, Team):
                project.team = last_model
                project.parent_project = None
            elif isinstance(last_model, Project):
                project.parent_project = last_model
                project.team = None
            # The path gets updated here
            project.index = index
            project.save()

            # Moving on to next children
            for num, next_child in enumerate(next_children):
                self.handle_children(next_child, project, num)
        # The child must be a subclass from Topic if it isn't a Project
        else:
            topic = self.topics[class_name].objects.get(_id=child["_id"])
            # Since topics always have a project parent
            topic.project = last_model
            topic.index = index
            # The path gets updated here
            topic.save()


    def update(self, request, team_id):
        """ Updates the models based on the input heirarchy """

        data = request.data

        initial_children = data["projects"]
        team = Team.objects.get(_id=data["_id"])

        for num, child in enumerate(initial_children):
            self.handle_children(child, team, num)

        team.save()
        return Response(TeamTreeSerializer(team).data)