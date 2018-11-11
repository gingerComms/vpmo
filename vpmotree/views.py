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
from vpmoauth.serializers import UserDetailsSerializer

from vpmotree.models import *
from vpmotree.serializers import *
from vpmotree.permissions import TeamPermissions, CreatePermissions, TaskListCreateAssignPermission
from vpmotree.filters import TeamListFilter, ReadNodeListFilter
from guardian import shortcuts

from datetime import datetime as dt


class FilteredTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, TeamPermissions]
    queryset = Team.objects.all()
    filter_backends = (TeamListFilter,)


class AllNodesListView(ListAPIView):
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


class NodeParentsListView(ListAPIView):
    """ Returns a list of all nodes in the path of the input node (including the input node itself) """

    serializer_class = MinimalNodeSerialiizer
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
        # print(node_path)
        try:
            nodes_in_path = TreeStructure.objects.filter(_id__in=node_path)
            # Sorting the nodes by index in the path
            nodes_in_path = sorted(nodes_in_path, key=lambda x: node_path.index(str(x._id)))
        except:
            print("EXCEPTION", node_path)
            raise

        return nodes_in_path


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
        serializer = TeamSerializer(data=data)
        if serializer.is_valid():
            team = serializer.save()
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
            "Deliverable": DeliverableSerializer
        }
        return mapped_classes[self.kwargs["nodeType"]]

    def create(self, request, nodeType, *args, **kwargs):
        data = request.data.copy()

        parent_node = TreeStructure.objects.get(_id=data.pop("parentID"))
        data["path"] = "{parent_path}{parent_id},".format(parent_path=parent_node.path or ",", parent_id=str(parent_node._id))

        serializer = self.get_serializer_class()(data=data)
        if serializer.is_valid():
            node = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveUpdateNodeView(RetrieveUpdateAPIView):

    def get_object(self):
        try:
            return TreeStructure.objects.get(_id=self.kwargs["nodeID"]).get_object()
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
            "Team": TeamSerializer
        }

        model = self.get_model()
        return mapped_classes[self.get_model().__name__]

    def partial_update(self, request, *args, **kwargs):
        """ This method gets called on a PATCH request - partially updates the model """
        node = self.get_object()
        if node is None:
            return Response({"message": "Node not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer_class()(node, data=request.data, partial=True)
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
        assert request.query_params.get("nodeType") in ["Project", "Team", "Topic"]

        try:
            node = TreeStructure.objects.get(_id=node_id)
        except TreeStructure.DoesNotExist:
            return Response({"message": "TreeStructure not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # Getting a dictionary of all users that have any permissions to the model
        raw_user_roles = UserRole.objects.filter(node=node).values("role_name", 
            "user___id", "user__email", "user__username", "user__fullname")

        # Rename the keys for easier access in the frontend
        user_roles = []
        for obj in raw_user_roles:
            user_roles.append({
                "_id": str(obj["user___id"]),
                "role": obj["role_name"],
                "email": obj["user__email"],
                "username": obj["user__username"],
                "fullname": obj["user__fullname"]
            })

        return Response(user_roles)

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
        elif "update_top_user_role" in  permissions and request.query_params["nodeType"] in Topic.topic_classes:
            assignable_roles += ["topic_viewer", "topic_contributor"]

        return Response(assignable_roles)


class AssignableTaskUsersView(ListAPIView):
    """ Returns a list of users that can be assigned a task for a given node """
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username",)

    def get_queryset(self):
        node = self.kwargs["nodeID"]
        try:
            node = TreeStructure.objects.get(_id=node)
            node = node.get_object()
        except TreeStructure.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        required_perm = "update_{}".format(node.node_type.lower())
        users_with_update_perms = UserRole.get_user_ids_with_heirarchy_perms(node, required_perm)

        return MyUser.objects.filter(_id__in=users_with_update_perms)


class AssignedTasksListView(ListAPIView):
    """ Returns a list of tasks for the current node """
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Task.objects.filter(node___id=self.kwargs["nodeID"]).order_by("-created_at")


class DeleteUpdateCreateTaskView(APIView):
    """ View that takes a post request for creating a Task object with the given data """
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, TaskListCreateAssignPermission,)

    def delete(self, request, *args, **kwargs):
        """ Deletes the input task """
        data = request.data.copy()
        try:
            task = Task.objects.get(_id=data["task"])
        except Task.DoesNotExist:
            return Response({'message': "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        task.delete()

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """ Handles updating the status of a task 
            NOTE - The reason this isn't merged into the put endpoint is because
                we need to handle different permissions for both tasks and combining the 
                endpoints would just make it messy
        """
        data = request.data.copy()
        try:
            task = Task.objects.get(_id=data["task"])
        except Task.DoesNotExist:
            return Response({'message': "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        if task.assignee != request.user:
            return Response({"message": "Only assignee can update task status"}, status=status.HTTP_403_FORBIDDEN)

        task.status = data["status"]
        task.save()

        return Response(self.serializer_class(task).data)


    def put(self, request, *args, **kwargs):
        """ Handles updating the assigning for a given task object """
        data = request.data.copy()

        try:
            assigning_to = MyUser.objects.get(username=data["assignee"])
        except MyUser.DoesNotExist:
            return Response({"message": "Assignee not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            task = Task.objects.get(_id=data["task"])
        except Task.DoesNotExist:
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        # The new assignee must have at least update_node permissions to node, or return 400
        assignee_perms = assigning_to.get_permissions(task.node)
        if not "update_{}".format(request.query_params["nodeType"].lower()) in assignee_perms:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        task.assignee = assigning_to
        task.save()

        data = self.serializer_class(task).data

        return Response(data)


    def post(self, request, *args, **kwargs):
        """ Handles Creating a task object """
        data = request.data.copy()
        # Defaulting created_by and assignee to the creator (request.user)
        data["created_by"] = str(request.user.pk)
        if not data.get("assignee", None):
            data["assignee"] = str(request.user.pk)
        else:
            data["assignee"] = MyUser.objects.get(username=data["assignee"])._id
        # Expecting the date to be input in this format
        data["due_date"] = dt.strptime(data["due_date"][:10], "%Y-%m-%d").strftime("%Y-%m-%d")

        data["status"] = "NEW"

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            task = serializer.save()
            data = serializer.data

            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
