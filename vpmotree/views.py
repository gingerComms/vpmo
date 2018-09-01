from django.db.models.functions import Length

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import filters
from rest_framework import status
from vpmoauth.models import MyUser

from vpmotree.models import *
from vpmotree.serializers import *
from vpmotree.permissions import TeamPermissions
from vpmotree.filters import TeamListFilter
from guardian import shortcuts


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
    queryset = Team.objects.all()


class CreateProjectView(CreateAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)


class CreateTeamView(CreateAPIView):
    model = Team
    serializer_class = TeamSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """ Handles creation of the team through the TeamSerializer """
        data = request.data.copy()
        data["user_team"] = request.data["name"] + "@" +request.user.username
        data["user_linked"] = False
        serializer = TeamSerializer(data=data)
        if serializer.is_valid():
            team = serializer.save()
            shortcuts.assign_perm("created_obj", request.user, team)
            request.user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeamTreeView(RetrieveUpdateAPIView):
    model = Team
    serializer_class = TreeStructureWithChildrenSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """ Returns the team object from the url id arg """
        try:
            team = Team.objects.get(_id=self.kwargs.get("team_id", None))
            return team
        except Team.DoesNotExist:
            return None


    def handle_children(self, child, parent, index):
        """ Takes a child as input and saves it using the parent's path and
            then moves on to the child's own children (if any)
        """
        next_children = child.get("children", [])

        # Saves the child using the parent and index in the array
        child = TreeStructure.objects.get(_id=child["_id"])
        child.index = index
        if parent.path is None:
            child.path = "," + str(parent._id) + ","
        else:
            child.path = parent.path + str(parent._id) + ","
        child.save()

        # Moves the loop onto the next children
        for index, next_child in enumerate(next_children):
            self.handle_children(next_child, child, index)


    def update(self, request, team_id):
        """ Updates the models based on the input hierarchy; takes a dictionary starting from a single team as input """
        data = request.data

        # The top most element is always a team, so second level is always projects
        initial_children = data["children"]
        team = Team.objects.get(_id=data["_id"])

        # Starting off the children loop
        for index, child in enumerate(initial_children):
            self.handle_children(child, team, index)

        return Response(TreeStructureWithChildrenSerializer(team).data)
