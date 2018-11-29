from django.shortcuts import render

from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from vpmoauth.serializers import UserDetailsSerializer
from vpmotask.permissions import TaskListCreateAssignPermission
from vpmotree.models import TreeStructure
from vpmotask.models import Task
from vpmotask.serializers import TaskSerializer, TaskListWithTasksSerializer
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
    permission_classes = (IsAuthenticated, TaskListCreateAssignPermission,)

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


class DeleteUpdateCreateTaskListView(APIView):
	""" Contains endpoints required for deleting/updating/creating
		Task lists
	"""
	permission_classes = (IsAuthenticated, TaskListCreateAssignPermission,)
	serializer_class = TaskListWithTasksSerializer

	def post(self, request):
		""" Handles creating a task list object """
		data = request.data.copy()

		serializer = self.serializer_class(TaskListWithTasksSerializer)
		if serializer.is_valid():
			task_list = serializer.save()

			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



