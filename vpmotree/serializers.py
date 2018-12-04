from django.utils import timezone
from rest_framework import serializers
from rest_framework import fields

from .models import Team, Project, Deliverable, Issue, Risk, Meeting, TreeStructure
from vpmoauth.models import UserRole, MyUser
from vpmotask.models import Task
from vpmoauth.serializers import UserDetailsSerializer
from vpmoprj.serializers import *

from django.apps import apps
from django.db.models import Q
from rest_framework.fields import CurrentUserDefault

import collections


class DashboardNodeBaseSerializer(serializers.Serializer):
    """ Contains all the generic count fields required in the node's
        Dashboard frontend pages
        Also contains a list of children nodeIDs that the user has access to
        which is used to calculate total unread messages for the node on the frontend
    """
    members_count = serializers.SerializerMethodField(required=False)
    topic_counts = serializers.SerializerMethodField(required=False)
    child_nodes = serializers.SerializerMethodField(required=False)

    def get_topic_counts(self, instance):
        """ Returns counts of different topic instances
            that have this node in their heirarchy
        """
        all_topics = TreeStructure.objects.filter(node_type="Topic", path__contains=instance._id) \
                        .values_list("model_name", flat=True)
        return collections.Counter(all_topics)

    def get_members_count(self, instance):
        """ Returns the count of users that have at least read permissions for this node """
        return len(UserRole.get_user_ids_with_heirarchy_perms(instance).distinct())

    def get_child_nodes(self, instance):
        """ Returns a list of nodes that the user has "update" access to under this node """
        return [str(i) for i in list(UserRole.get_assigned_nodes(self.context["request"].user, str(instance._id)).distinct())]


class ProjectSerializer(DashboardNodeBaseSerializer, serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    project_owner = serializers.SerializerMethodField(required=False)
    start = serializers.DateField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"], allow_null=True, required=False)
    finish = serializers.DateField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"], allow_null=True, required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)

    # Counts for the frontend
    tasks_overdue_count = serializers.SerializerMethodField(required=False)
    tasks_due_count = serializers.SerializerMethodField(required=False)

    def get_tasks_overdue_count(self, instance):
        """ Returns tasks that belong to a node under this project (or this project itself)
            that have a due date earlier than right now
        """
        node_condition = Q(node__path__contains=instance._id) | Q(node___id=instance._id)
        return Task.objects.filter(node_condition, due_date__lte=timezone.now().date()) \
                    .values("title", "assignee___id")

    def get_tasks_due_count(self, instance):
        """ Returns tasks that belong to a node under this project (or this project itself)
            that have a due date later than right now
        """
        node_condition = Q(node__path__contains=instance._id) | Q(node___id=instance._id)
        return Task.objects.filter(node_condition, due_date__gte=timezone.now().date()) \
                    .values("title", "assignee___id")

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_project_owner(self, instance):
        if instance.project_owner:
            return str(instance.project_owner)
        return None

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "content", "start", "finish", "project_owner", "path", "index", "node_type",
                "created_at", "user_permissions", "user_role", "members_count", "topic_counts", "child_nodes",
                "tasks_overdue_count", "tasks_due_count"]


class TeamSerializer(DashboardNodeBaseSerializer, serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)
    _id = ObjectIdField(read_only=True)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)
    projects_count = serializers.SerializerMethodField(required=False)

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_projects_count(self, instance):
        return TreeStructure.objects.filter(node_type="Project", path__contains=instance._id).count()

    class Meta:
        model = Team
        fields = ["_id", "name", "user_linked", "created_at", "updated_at", "user_team",
                "node_type", "user_permissions", "user_role", "members_count", "topic_counts", "projects_count",
                "child_nodes"]


class DeliverableSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    due_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"], allow_null=True, required=False)
    topic_type = serializers.SerializerMethodField(required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_topic_type(self, obj):
        return "Deliverable"

    class Meta:
        model = Deliverable
        fields = ["_id", "name", "node_type", "path", "index", "due_date", "content", "topic_type",
                "user_permissions", "user_role"]


class IssueSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    due_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"], allow_null=True, required=False)
    assignee = UserDetailsSerializer(required=False, allow_null=True)
    topic_type = serializers.SerializerMethodField(required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_topic_type(self, obj):
        return "Issue"

    def get_assignee_name(self, instance):
        try:
            return instance.assignee.fullname
        except:
            return None

    def validate(self, data):
        # Getting the assignee from the initial data passed into serializer
        assignee_id = self.initial_data.get("assignee_id", None)
        # Validating the rest of the fields
        data = super(IssueSerializer, self).validate(data)
        # Setting the foreign key
        if assignee_id:
            data["assignee"] = MyUser.objects.get(_id=assignee_id)
        return data

    class Meta:
        model = Issue
        fields = ["_id", "name", "node_type", "path", "index", "due_date", "content", "severity", "assignee",
                "topic_type", "user_permissions", "user_role"]


class RiskSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    due_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"], allow_null=True, required=False)
    assignee = UserDetailsSerializer(required=False, allow_null=True)
    topic_type = serializers.SerializerMethodField(required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_topic_type(self, obj):
        return "Risk"

    def get_assignee_name(self, instance):
        try:
            return instance.assignee.fullname
        except:
            return None

    def validate(self, data):
        # Getting the assignee from the initial data passed into serializer
        assignee_id = self.initial_data.get("assignee_id", None)
        # Validating the rest of the fields
        data = super(RiskSerializer, self).validate(data)
        # Setting the foreign key
        if assignee_id:
            data["assignee"] = MyUser.objects.get(_id=assignee_id)
        return data

    class Meta:
        model = Risk
        fields = ["_id", "name", "node_type", "path", "index", "due_date", "content", "impact", "probability", "assignee",
                "topic_type", "user_permissions", "user_role"]


class MeetingSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    date_time = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"], allow_null=False, required=True)
    topic_type = serializers.SerializerMethodField(required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    user_role = serializers.SerializerMethodField(required=False)

    def get_user_permissions(self, instance):
        return self.context["request"].user.get_permissions(instance)

    def get_user_role(self, instance):
        role = self.context["request"].user.get_role(instance)
        return role.role_name if role else None

    def get_topic_type(self, obj):
        return "Meeting"

    def validate(self, data):
        # Validating the rest of the fields
        data = super(MeetingSerializer, self).validate(data)
        # Setting the foreign key
        return data

    class Meta:
        model = Meeting
        fields = ["_id", "name", "node_type", "path", "index", "date_time", "content", "venue",
                "topic_type", "user_permissions", "user_role"]


class TreeStructureWithoutChildrenSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    node_type = serializers.CharField(max_length=48)
    name = serializers.CharField(max_length=150)
    model_name = serializers.CharField(max_length=48)

    # def get_name(self, instance):
    #     if instance._meta.model == TreeStructure:
    #         return instance.get_object().name
    #     return instance.name

class TreeStructureWithChildrenSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    name = serializers.CharField(max_length=150)
    children = serializers.SerializerMethodField()
    node_type = serializers.CharField(max_length=48)
    model_name = serializers.CharField(max_length=48)

    # def get_name(self, instance):
    #     if instance._meta.model == TreeStructure:
    #         return instance.get_object().name
    #     return instance.name

    def get_branch_extensions(self, branch, branch_level):
        """ Takes a branch as input and starts the loop for either the next branches (if they exist) or the leaves """
        next_level = branch_level + 1
        # Finding children on the next level with the current branch._id in the path
        children = filter(lambda x: x["path"].count(',') == next_level and str(branch["_id"]) in x["path"], self.all_children)
        children = sorted(children, key=lambda x: x["index"])
        for child in children:
            child["children"] = self.get_branch_extensions(child, next_level)

        return children


    def get_children(self, instance):
        """ Takes a team as input and returns the Tree it is the root of """
        children = []

        self.user =  self.context['request'].user

        permissions = self.user.get_permissions(instance, all_types=True)
        allowed_node_types = [i.split("_")[-1].capitalize() for i in permissions if "read_" in i]

        child_condition = Q(path__startswith=","+str(instance._id)) | Q(path__icontains=str(instance._id))
        role_condition = Q(node_type__in=allowed_node_types) | Q(user_role_node__user=self.user)
        
        self.all_children = TreeStructure.objects.filter(child_condition, role_condition).distinct()

        if instance.node_type == "Team":
            # All objects starting from the current ROOT (Team)
            self.all_children = TreeStructureWithoutChildrenSerializer(self.all_children.filter(
                node_type="Project"), many=True).data
            # Finding the first branches from the root (Projects)
            top_level = 2
        else:
            if instance.node_type == "Project":
                self.all_children = TreeStructureWithoutChildrenSerializer(self.all_children, many=True).data
                top_level = instance.path.count(",") + 1

        first_branches = filter(lambda x: x["path"].count(",") == top_level, self.all_children)
        first_branches = sorted(first_branches, key=lambda x: x["index"])

        for branch in first_branches:
            branch["children"] = self.get_branch_extensions(branch, top_level)
            children.append(branch)

        return children


class NodeParentsSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    node = serializers.SerializerMethodField()
    immediate_parent = serializers.SerializerMethodField()
    root = serializers.SerializerMethodField()

    def get_node(self, instance):
        return MinimalNodeSerializer(instance).data

    def get_immediate_parent(self, instance):
        if instance.path is None:
            return None
        split_path = list(filter(lambda x: x.strip(), instance.path.split(',')))
        if len(split_path) <= 2:
            return None
        parent = TreeStructure.objects.get(_id=split_path[-1])
        return MinimalNodeSerializer(parent).data

    def get_root(self, instance):
        if instance.path is None:
            return MinimalNodeSerializer(instance).data
        split_path = list(filter(lambda x: x.strip(), instance.path.split(',')))
        parent = TreeStructure.objects.get(_id=split_path[0])
        return MinimalNodeSerializer(parent).data
