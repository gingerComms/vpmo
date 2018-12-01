from django.shortcuts import render
from django.db import transaction

from rest_framework import generics, status, filters, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from vpmoauth.serializers import UserDetailsSerializer
from vpmotask.permissions import *
from vpmotree.models import TreeStructure, Project
from vpmotask.models import Task, ScrumboardTaskList
from vpmotask.serializers import *
from vpmoauth.models import MyUser, UserRole

from datetime import datetime as dt

# Create your views here.
class AssignableTaskUsersView(generics.ListAPIView):
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


class AssignedTasksListView(generics.ListAPIView):
    """ Returns a list of tasks for the current node """
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Task.objects.filter(node___id=self.kwargs["nodeID"]).order_by("-created_at")


class DeleteUpdateCreateTaskView(APIView):
    """ View that takes a post request for creating a Task object with the given data """
    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, TaskPermission,)

    def delete(self, request, *args, **kwargs):
        """ Deletes the input task """
        data = request.data.copy()
        try:
            task = Task.objects.get(_id=data["_id"])
        except Task.DoesNotExist:
            return Response({'message': "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        task.delete()

        return Response(status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """ Handles updating the status of a task 
            NOTE - The reason this isn't merged into the put endpoint is because
                we need to handle different permissions for both tasks and combining the 
                endpoints would just make it messy
            Also used to when the task is rearranged in a list/moved to a different list
        """
        data = request.data.copy()
        try:
            task = Task.objects.get(_id=data["_id"])
        except Task.DoesNotExist:
            return Response({'message': "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        if task.assignee != request.user:
            return Response({"message": "Only assignee can partially update the task"}, status=status.HTTP_403_FORBIDDEN)

        # Partially updating the task
        serializer = self.serializer_class(task, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, *args, **kwargs):
        """ Handles updating the assigning for a given task object """
        data = request.data.copy()

        try:
            assigning_to = MyUser.objects.get(username=data.pop("assignee"))
        except MyUser.DoesNotExist:
            return Response({"message": "Assignee not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            task = Task.objects.get(_id=data.pop("_id", None))
        except Task.DoesNotExist:
            return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        # The new assignee must have at least update_node permissions to node, or return 400
        assignee_perms = assigning_to.get_permissions(task.node)
        if not "update_{}".format(request.query_params["nodeType"].lower()) in assignee_perms:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Partially updating the task
        data["assignee_id"] = assigning_to._id
        serializer = self.serializer_class(task, data=data, partial=True)
        if serializer.is_valid():
            task = serializer.save()
            return Response(self.serializer_class(task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        """ Handles Creating a task object """
        data = request.data.copy()
        # Defaulting created_by and assignee to the creator (request.user)
        data["created_by"] = str(request.user.pk)
        assignee = data.pop("assignee", None)
        if not assignee:
            data["assignee_id"] = str(request.user._id)
        else:
            data["assignee_id"] = MyUser.objects.get(username=assignee)._id
        # Expecting the date to be input in this format
        data["due_date"] = dt.strptime(data["due_date"][:10], "%Y-%m-%d").strftime("%Y-%m-%d")

        data["status"] = "NEW"

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            task = serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScrumboardTaskListView(APIView):
    """ Contains endpoints required for deleting/partially updating/creating
        Task lists
    """
    permission_classes = (IsAuthenticated, TaskListPermission,)
    serializer_class = ScrumboardTaskListWithTasksSerializer

    def post(self, request):
        """ Handles creating a task list object """
        data = request.data.copy()

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            task_list = serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """ Handles partially updating a task list object """
        data = request.data.copy()

        # Getting the task from the query parameter
        try:
            task_list = ScrumboardTaskList.objects.get(_id=request.query_params["task_list"])
        except ScrumboardTaskList.DoesNotExist:
            return Response({"message": "Task list does not exist"}, status=HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(task_list, data=data, partial=True)
        if serializer.is_valid():
            task_list = serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """ Deletes the task list object in the data """
        data = request.data.copy()
        try:
            task_list = ScrumboardTaskList.objects.get(_id=data["_id"])
        except ScrumboardTaskList.DoesNotExist:
            return Response({'message': "Task List not found"}, status=status.HTTP_404_NOT_FOUND)

        task_list.delete()

        return Response(status=status.HTTP_200_OK)


class TaskIndexUpdateView(generics.UpdateAPIView):
    """ Updates the index(es) and task list of all tasks in a scrumboard-list """
    permission_classes = (IsAuthenticated, TaskReorderPermissions,)
    serializer_class = TaskListSerializer

    def get_object(self):
        try:
            return ScrumboardTaskList.objects.get(_id=self.kwargs["task_list_id"])
        except ScrumboardTaskList.DoesNotExist:
            return None

    def put(self, request, task_list_id):
        """ Updates the indexes of tasks in a list based on the input order """
        task_ids = [str(i["_id"]) for i in request.data.copy()]

        task_list = self.get_object()
        if task_list is None:
            return Response({"message": "Task list does not exist"}, status=HTTP_404_NOT_FOUND)

        tasks = Task.objects.filter(_id__in=task_ids)

        # We don't need to explicitly remove the tasks to this task list since they should have been removed
        #   removed in another api call at that point
        tasks.update(task_list=task_list)

        with transaction.atomic():
            for task in tasks:
                task.task_list_index = task_ids.index(str(task._id))
                task.save()

        return Response(self.serializer_class(tasks.order_by("task_list_index"), many=True).data)


class ProjectScrumboardTaskListView(mixins.UpdateModelMixin, generics.ListAPIView):
    """ Returns all task lists for the given project, ordered by the index
        NOTE - For implementation, onInit of the projectScrumboard component in the frontend
            call this endpoint with the project id as input to get all task lists
    """
    permission_classes = (IsAuthenticated, NodeUpdateLevelPermissions)
    serializer_class = ScrumboardTaskListWithTasksSerializer

    def put(self, request, node_id):
        """ Updates the index of all project task-lists
            based on the order of appearance in the input task-lists array
        """
        to_update = self.get_queryset()

        index_order = [str(i["_id"]) for i in request.data]

        with transaction.atomic():
            for i in to_update:
                i.index = index_order.index(str(i._id))
                i.save()

        return Response(self.serializer_class(to_update.order_by("index"), many=True).data)

    # TODO: Create update endpoint to update index of all task lists under a project
    #   Use that in the frontend
    #   The same will need to be done for tasks in a task list as well.

    def get_queryset(self):
        try:
            project = Project.objects.get(_id=self.kwargs["node_id"])
        except Project.DoesNotExist:
            return Response({"message": "Project not found"}, status=status.HTTP_404_NOT_FOUND)

        return ScrumboardTaskList.objects.filter(project=project).order_by("index")


class AssignableScrumboardListsView(generics.ListAPIView):
    """ Returns the lists assigined to the first project in
        the given node's tree branch.
        For project level nodes, the lists assigned are the lists in 
            the project itself.
        For topic level nodes, the lists assigned are the lists in
            *** the last node in the topic's path ** since the parent of
            all topics is a project
    """
    permission_classes = (IsAuthenticated, NodeUpdateLevelPermissions)
    serializer_class = ScrumboardTaskListMinimalSerializer

    def get_node(self):
        """ Returns the node defined in the url parameter """
        try:
            return TreeStructure.objects.get(_id=self.kwargs["node_id"])
        except TreeStructure.DoesNotExist:
            return None

    def get_queryset(self):
        node = self.get_node()
        if node is None:
            return Response({"message": "Node not found"}, status=status.HTTP_404_NOT_FOUND)

        # Conditional using the logic defined in the doc string
        if node.node_type == "Project":
            project_id = node._id
        elif node.node_type == "Topic":
            project_id = node.path.split(",")[-2]
        else:
            return Response({"message": "Tasks can only be created for Projects and Topics"}, status=status.HTTP_400_BAD_REQUEST)

        return ScrumboardTaskList.objects.filter(project___id=project_id).order_by("index")



