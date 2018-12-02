from rest_framework import serializers

from vpmoprj.serializers import *
from vpmotree.models import TreeStructure, Project
from vpmoauth.models import MyUser
from vpmoauth.serializers import UserDetailsSerializer
from vpmotask.models import Task, ScrumboardTaskList
from vpmodoc.models import TaskDocument
from vpmodoc.serializers import TaskDocumentMinimalSerializer


class ScrumboardTaskListMinimalSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    project = RelatedObjectIdField(queryset=Project.objects.all())

    class Meta:
        model = ScrumboardTaskList
        fields = "__all__"


class ScrumboardTaskListWithTasksSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    tasks = serializers.SerializerMethodField(required=False)
    project = RelatedObjectIdField(queryset=Project.objects.all(), required=False)

    def get_tasks(self, instance):
        """ Contains a list of tasks assigned to this node """
        return TaskListSerializer(Task.objects.filter(task_list=instance).order_by("task_list_index"), many=True).data

    def validate(self, data):
        project_id = self.initial_data.get("project_id", None)

        super(ScrumboardTaskListWithTasksSerializer, self).validate(data)

        if project_id:
            data["project"] = Project.objects.get(_id=project_id)

        return data

    class Meta:
        model = ScrumboardTaskList
        fields = ("_id", "title", "index", "tasks", "project")


class TaskListSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    node = RelatedObjectIdField(queryset=TreeStructure.objects.all())
    created_by = RelatedObjectIdField(queryset=MyUser.objects.all())
    assignee = UserDetailsSerializer(required=False)
    due_date = serializers.DateField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"], allow_null=True, required=False)
    task_list = RelatedObjectIdField(queryset=ScrumboardTaskList.objects.all())
    documents = serializers.SerializerMethodField(required=False)

    def get_documents(self, instance):
        queryset = TaskDocument.objects.filter(task=instance)
        return TaskDocumentMinimalSerializer(queryset, many=True).data

    class Meta:
        model = Task
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    node = RelatedObjectIdField(queryset=TreeStructure.objects.all())
    created_by = RelatedObjectIdField(queryset=MyUser.objects.all())
    assignee = UserDetailsSerializer(required=False)
    due_date = serializers.DateField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"], allow_null=True, required=False)
    task_list = ScrumboardTaskListMinimalSerializer(required=False)

    def validate(self, data):
        # Getting the assignee from the initial data passed into serializer
        assignee_id = self.initial_data.get("assignee_id", None)
        # Getting the task_list id
        task_list_id = self.initial_data.get("task_list_id", None)
        # Validating the rest of the fields
        data = super(TaskSerializer, self).validate(data)
        # Setting the foreign key
        if assignee_id:
            data["assignee"] = MyUser.objects.get(_id=assignee_id)
        if task_list_id:
            data["task_list"] = ScrumboardTaskList.objects.get(_id=task_list_id)

        return data

    class Meta:
        model = Task
        fields = "__all__"
