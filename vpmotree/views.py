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
from vpmoauth.serializers import UserDetailsSerializer, AllUsersSerializer

from vpmotree.models import *
from vpmotree.serializers import *
from vpmotree.permissions import TeamPermissions, \
                                CreatePermissions, \
                                GeneralNodePermission
from vpmotree.filters import ReadNodeListFilter

from datetime import datetime as dt


class AllNodesListView(ListAPIView):
    """ Returns all nodes that the user has access to
        if a nodeParent query parameter is provided, returns all 
        nodes that the user has access to and have the given parent
        as the last _id in the path
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [ReadNodeListFilter]

    serializers = {
        "Team": TeamSerializer,
        "Project": ProjectSerializer,
        "Deliverable": DeliverableSerializer,
        "Issue": IssueSerializer,
        "Risk": RiskSerializer,
        "Meeting": MeetingSerializer
    }

    def get_queryset(self):
        model = apps.get_model("vpmotree", self.request.query_params["nodeType"])

        # Filtering by node parent if query is provided
        if self.request.query_params.get("parentNode", None):
            return model.objects.filter(path__endswith=self.request.query_params["parentNode"])

        return model.objects.all()

    def get_serializer_class(self):
        return self.serializers[self.request.query_params["nodeType"]]


class NodeParentsListView(ListAPIView):
    """ Returns a list of all nodes in the path of the input node (including the input node itself) """

    serializer_class = MinimalNodeSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """ Returns the node object from the url id arg """
        try:
            node = TreeStructure.objects.get(_id=self.kwargs.get("nodeID", None))
        except TreeStructure.DoesNotExist:
            return []
        # If the node's path is None (node is a team) return just the node
        if node.path is None:
            return [node]

        # Otherwise, return all nodes in the node's path
        node_path = list(filter(lambda x: x.strip(), node.path.split(',')))
        node_path.append(str(node._id))
        
        nodes_in_path = TreeStructure.objects.filter(_id__in=node_path)
        # Sorting the nodes by index in the path
        nodes_in_path = sorted(nodes_in_path, key=lambda x: node_path.index(str(x._id)))

        return nodes_in_path


class AllProjectsView(ListAPIView):
    # LEGACY VIEW - MAY BE REMOVED
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [ReadNodeListFilter,]
    queryset = Project.objects.all()


class AllTeamsView(ListAPIView):
    # LEGACY VIEW - MAY BE REMOVED
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    queryset = Team.objects.all()


class CreateProjectView(CreateAPIView):
    """ LEGACY VIEW - MAY BE REMOVED """
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, CreatePermissions,)

    def post(self, request, *args, **kwargs):
        """ Handles creation of the project through the ProjectSerializer """
        data = request.data.copy()
        parent = TreeStructure.objects.get(_id=data.pop("parent"))
        data["path"] = parent.path or "," + str(parent._id) + ","
        # add team_project unique value based on project name @ team unique name
        # data["team_project"] = request.data["name"] + "@" + request.
        serializer = ProjectSerializer(data=data)
        if serializer.is_valid():
            project = serializer.save()
            project.create_channel()
            project.update_channel_access()

            request.user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTeamView(CreateAPIView):
    model = Team
    serializer_class = TeamSerializer
    # Any authenticated user is allowed to create teams
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """ Handles creation of the team through the TeamSerializer """
        data = request.data.copy()
        data["user_team"] = request.data["name"] + "@" +request.user.username
        data["user_linked"] = False
        data = {
            "name": request.data["name"],
            "user_linked": False,
            "user_team": "{team_name}@{user_name}".format(team_name=request.data["name"], user_name=request.user.username)
        }
        serializer = TeamSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            team = serializer.save()
            team.create_channel()
            request.user.save()
            request.user.assign_role("team_admin", team)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateNodeView(CreateAPIView):
    """ Creates all node types that fall under a treestructure except Teams """
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        """ Returns the serializer responsible for creating the current node """
        mapped_classes = {
            "Project": ProjectSerializer,
            "Deliverable": DeliverableSerializer,
            "Issue": IssueSerializer,
            "Risk": RiskSerializer,
            "Meeting": MeetingSerializer
        }
        return mapped_classes[self.kwargs["nodeType"]]

    def create(self, request, nodeType, *args, **kwargs):
        data = request.data.copy()

        parent_node = TreeStructure.objects.get(_id=data.pop("parentID"))
        data["path"] = "{parent_path}{parent_id},".format(parent_path=parent_node.path or ",", parent_id=str(parent_node._id))

        serializer = self.get_serializer_class()(data=data, context={"request": request})
        if serializer.is_valid():
            node = serializer.save()
            node.save()
            node.create_channel()
            node.update_channel_access()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveUpdateNodeView(RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, GeneralNodePermission)

    def get_object(self):
        try:
            node = TreeStructure.objects.get(_id=self.kwargs["nodeID"]).get_object()
            self.check_object_permissions(self.request, node)
            return node
        except TreeStructure.DoesNotExist:
            return None

    def get_model(self):
        node = TreeStructure.objects.get(_id=self.kwargs["nodeID"])
        return node.get_model_class()

    def get_serializer_class(self):
        """ Returns the serializer responsible for creating the current node """
        mapped_classes = {
            "Project": ProjectSerializer,
            "Deliverable": DeliverableSerializer,
            "Team": TeamSerializer,
            "Issue": IssueSerializer,
            "Risk": RiskSerializer,
            "Meeting": MeetingSerializer
        }

        model = self.get_model()
        return mapped_classes[self.get_model().__name__]

    def partial_update(self, request, *args, **kwargs):
        """ This method gets called on a PATCH request - partially updates the model """
        node = self.get_object()
        if node is None:
            return Response({"message": "Node not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        # Taking out _id from the input data if it's there (not needed since this is a partial update)
        if "_id" in data.keys():
            _id = data.pop("_id")
            
        serializer = self.get_serializer_class()(node, data=data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodeTreeView(RetrieveUpdateAPIView):
    model = TreeStructure
    serializer_class = TreeStructureWithChildrenSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """ Returns the node object from the url id arg """
        try:
            node = TreeStructure.objects.get(_id=self.kwargs.get("nodeID", None))
            return node
        except TreeStructure.DoesNotExist:
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


    def update(self, request, nodeID):
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
        """
        if nodes[0]["path"] is not None:
            team_id = nodes[0]["path"].split(",")[1]
        else:
            team_id = nodes[0]["_id"]
        """
        node = self.get_object()
        return Response(TreeStructureWithChildrenSerializer(node, context={"request": request}).data)


class CreateDeliverableView(CreateAPIView):
    model = Deliverable
    serializer_class = DeliverableSerializer
    permission_classes = (IsAuthenticated,)


class CreateIssueView(CreateAPIView):
    model = Issue
    serializer_class = IssueSerializer
    permission_classes = (IsAuthenticated,)


class NodePermissionsView(APIView):
    """ Returns a list of user-role map for a particular node of given nodeType """

    def get(self, request, node_id):
        assert request.query_params.get("nodeType") in ["Project", "Team", "Topic"]

        try:
            node = TreeStructure.objects.get(_id=node_id)
        except TreeStructure.DoesNotExist:
            return Response({"message": "TreeStructure not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # Getting a dictionary of all users that have any permissions to the model
        raw_user_roles = UserRole.objects.filter(node=node).values("role_name", "user___id")
        raw_user_roles = {str(i["user___id"]): i["role_name"] for i in raw_user_roles}

        assigned_users = MyUser.objects.filter(_id__in=raw_user_roles.keys())

        data = AllUsersSerializer(assigned_users, many=True).data

        # Adding the user role into the data
        for i in data:
            i["role"] = raw_user_roles[str(i["_id"])]

        return Response(data)

class AssignableRolesView(APIView):
    """ Returns a list of roles assignable by a user for a node """
    permission_classes = (IsAuthenticated,)

    def get(self, request, node_id):
        try:
            node = TreeStructure.objects.get(_id=node_id)
            node = node.get_object()
        except TreeStructure.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        permissions = list(request.user.get_permissions(node, all_types=True))

        assignable_roles = []

        model = node.get_model_class()
        if "update_team_user_role" in permissions and model == Team:
            assignable_roles += ["team_member", "team_lead", "team_admin"]
        elif "update_project_user_role" in permissions and model == Project:
            assignable_roles += ["project_viewer", "project_contributor", "project_admin"]
        elif "update_topic_user_role" in  permissions and request.query_params["nodeType"] in Topic.topic_classes:
            assignable_roles += ["topic_viewer", "topic_contributor"]

        return Response(assignable_roles)