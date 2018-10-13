from django.db.models.functions import Length
from django.apps import apps

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework import filters
from rest_framework import status
from vpmoauth.models import MyUser, UserRole

from vpmotree.models import *
from vpmotree.serializers import *
from vpmotree.permissions import TeamPermissions
from vpmotree.filters import TeamListFilter, ReadNodeListFilter
from guardian import shortcuts

from datetime import datetime as dt


class FilteredTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, TeamPermissions]
    queryset = Team.objects.all()
    filter_backends = (TeamListFilter,)


class AllNodesView(ListAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [ReadNodeListFilter]

    serializers = {
        "Team": TeamSerializer,
        "Project": ProjectSerializer,
        "Deliverable": DeliverableSerializer
    }

    def get_queryset(self):
        model = apps.get_model("vpmotree", self.request.query_params["nodeType"])
        return model.objects.all()

    def get_serializer_class(self):
        return self.serializers[self.request.query_params["nodeType"]]


class AllProjectsView(ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ReadNodeListFilter,]
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
            request.user.save()
            request.user.assign_role("team_admin", team)
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
        try:
            filter_d["node"] = TreeStructure.objects.get(_id=node_id)
        except TreeStructure.DoesNotExist:
            return None

        if earlier_than is not None:
            earlier_msg = Message.objects.get(_id=earlier_than)
            filter_d["sent_on__lt"] = earlier_msg.sent_on

        messages = Message.objects.filter(**filter_d).order_by("-sent_on")[:20]
        messages = sorted(messages, key=lambda x: x.sent_on)

        return messages


class NodePermissionsView(APIView):
    """ Returns a list of user-role map for a particular node of given nodeType """

    def get(self, request, node_id):
        assert request.query_params.get("nodeType") in ["Project", "Team", "Deliverable"]
        # Fetching the node using the node_id and nodeType
        node_type = globals()[request.query_params.get("nodeType")]
        try:
            node = node_type.objects.get(_id=node_id)
        except node_type.DoesNotExist:
            return Response({"message": "{} not found.".format(request.query_params["nodeType"])},
                            status=status.HTTP_404_NOT_FOUND)

        # Getting a dictionary of all users that have any permissions to the model
        raw_user_roles = UserRole.objects.filter(node=node).values("role_name", 
            "user___id", "user__email", "user__username", "user__fullname")

        # Rename the keys for easier access in the frontend
        user_roles = []
        for obj in raw_user_roles:
            user_roles.append({
                "_id": obj["user___id"],
                "role": obj["role_name"],
                "email": obj["user__email"],
                "username": obj["user__username"],
                "fullname": obj["user__fullname"]
            })

        return Response(user_roles)

        return Response(user_roles)


class AssignableRolesView(APIView):
    """ Returns a list of roles assignable by a user for a node """
    permission_classes = (IsAuthenticated,)

    def get(self, request, node_id):
        model = apps.get_model("vpmotree", request.query_params["nodeType"])
        try:
            node = model.objects.get(_id=node_id)
        except model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        permissions = request.user.get_permissions(node)

        assignable_roles = []

        if "update_team_user_role" in permissions and model == Team:
            assignable_roles += ["team_member", "team_lead", "team_admin"]
        elif "update_project_user_role" in permissions and model == Project:
            assignable_roles += ["project_viewer", "project_contributor", "project_admin"]
        elif "update_top_user_role" in  permissions and request.query_params["nodeType"] in Topic.topic_classes:
            assignable_roles += ["topic_viewer", "topic_contributor"]

        return Response(assignable_roles)