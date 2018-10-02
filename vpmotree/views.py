from django.db.models.functions import Length

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView, get_object_or_404
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

    def post(self, request, *args, **kwargs):
        """ Handles creation of the project through the ProjectSerializer """
        data = request.data.copy()
        # add team_project unique value based on project name @ team unique name
        # data["team_project"] = request.data["name"] + "@" + request.
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            project = serializer.save()
            shortcuts.assign_perm("created_obj", request.user, project)
            request.user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class UpdateProjectView(RetrieveUpdateAPIView):
    queryset = Project
    serializer_class = ProjectSerializer
    lookup_field = "_id"

    def partial_update(self, request, _id, *args, **kwargs):
        """ This method gets called on a PATCH request - partially updates the model """
        try:
            project = Project.objects.get(_id=_id)
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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


    def handle_children(self, child, parent, index=None, all_children=[]):
        """ Takes a child as input and saves it using the parent's path and
            then moves on to the child's own children (if any)
        """
        # Update index if provided
        if index:
            child.index = index
        # Set the child's path using the parent's path
        if parent.path is None:
            # This conditional is mostly unnecessary at this point, but kept because it might come in handy
            # In the future
            child.path = "," + str(parent._id) + ","
        else:
            child.path = parent.path + str(parent._id) + ","
        child.save()

        # Fetching direct children of current child
        if all_children is None:
            all_children = TreeStructure.objects.filter(path__contains=child._id)
        next_children = self.get_direct_children(child._id)
        # Moves the loop onto the next children
        for next_child in next_children:
            self.handle_children(next_child, child, all_children=all_children)


    def get_direct_children(self, node_id, all_children=None):
        """ Returns all direct children of a node given the node _id """
        if all_children is None:
            all_children = TreeStructure.objects.filter(path__contains=node_id)

        # A direct child is a child which has the node's _id as the last _id in its path
        return list(filter(lambda x: str(x.path.split(",")[-2]) == str(node_id), all_children))


    def update(self, request, team_id):
        """ Updates the models based on the input hierarchy; takes a dictionary starting from a single team as input """
        # request.data should be an array of nodes
        nodes = request.data

        if not nodes:
            return Response({"message": "Please have at least one node in the update request"}, status=status.HTTP_400_BAD_REQUEST)

        for obj in nodes:
            node = TreeStructure.objects.get(_id=obj["_id"])
            node.index = obj["index"]
            node.save()
            if obj["path"] != node.path:
                # Since path was updated, update the node's path and all children as well
                node.path = obj["path"]
                node.save()
                # Getting all direct children
                all_children = TreeStructure.objects.filter(path__contains=node._id)
                # All children is passed to all sub-methods to avoid having to make repeated Database queries
                direct_children = self.get_direct_children(node._id, all_children=all_children)
                for child in direct_children:
                    self.handle_children(child, node, all_children=all_children)


        # The top most element is always a team, so second level is always projects
        if nodes[0]["path"] is not None:
            team_id = nodes[0]["path"].split(",")[1]
        else:
            team_id = nodes[0]["_id"]
        team = Team.objects.get(_id=team_id)
        return Response(TreeStructureWithChildrenSerializer(team).data)


class ProjectTreeView(TeamTreeView):
    model = Project

    def get_object(self):
        """ Returns the project object from the url id arg """
        try:
            project = Project.objects.get(_id=self.kwargs.get("project_id", None))
            return project
        except Project.DoesNotExist:
            return None

"""
class UpdateProjectView(RetrieveUpdateAPIView):
    model = Project
    serializers_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        try:
            project = Project.objects.get(_id=self.kwargs.get("Project_id", None))
            return project
        except Project.DoesNotExist:
            return None


    def update(self, request, *args, **kwargs):
        project = Project.objects.get(_id=self.kwargs.get("Project_id", None))
        project.name = self.request.data["name"]
        project.save()
        return Response(ProjectSerializer(project).data)
"""


class CreateDeliverableView(CreateAPIView):
    model = Deliverable
    serializer_class = DeliverableSerializer
    permission_classes = (IsAuthenticated,)


class MessageListView(ListAPIView):
    model = Message
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        earlier_than = self.request.query_params.get('earlier_than', None)
        node_id = self.kwargs["node_id"]

        filter_d = {}
        filter_d["path__endswith"] = node_id+","

        if earlier_than is not None:
            filter_d["sent_on__lte"] = dt.strptime(earlier_than, "%m-%d-%Y")

        return Message.objects.filter(**filter_d).order_by("sent_on")[:20]