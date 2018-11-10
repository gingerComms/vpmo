from rest_framework import serializers
from rest_framework import fields
from .models import Team, Project, Deliverable, TreeStructure, Message, Topic, Task
from vpmoauth.models import UserRole, MyUser
from django.apps import apps
from django.db.models import Q
from rest_framework.fields import CurrentUserDefault


class RelatedObjectIdField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return str(value)

class ObjectIdField(serializers.IntegerField):
    def to_representation(self, value):
        return str(value)

class TaskSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    node = RelatedObjectIdField(queryset=TreeStructure.objects.all())
    created_by = RelatedObjectIdField(queryset=MyUser.objects.all())
    assignee = RelatedObjectIdField(queryset=MyUser.objects.all())

    class Meta:
        model = Task
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    author = serializers.CharField(source="author.username", required=False)

    class Meta:
        model = Message
        fields = ["_id", "author", "content", "sent_on"]


class ProjectSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    project_owner = serializers.SerializerMethodField(required=False)
    start = serializers.DateField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"], allow_null=True, required=False)

    def get_project_owner(self, instance):
        if instance.project_owner:
            return str(instance.project_owner)
        return None

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "content", "start", "project_owner", "path", "index"]


class TeamSerializer(serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)
    _id = ObjectIdField(read_only=True)

    class Meta:
        model = Team
        fields = ["_id", "name", "user_linked", "created_at", "updated_at", "user_team"]


class DeliverableSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    due_date = serializers.DateTimeField(input_formats=["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S"], allow_null=True, required=False)
    
    class Meta:
        model = Deliverable
        fields = ["_id", "name", "node_type", "path", "index", "due_date"]


# class ProjectTreeSerializer(serializers.ModelSerializer):
#     _id = serializers.SerializerMethodField(required=False)
#
#     def get__id(self, instance):
#         return str(instance._id)
#
#     class Meta:
#         model = Project
#         fields = ["_id", "name", "description", "node_type", "path", "index"]


# class TeamTreeSerializer(serializers.ModelSerializer):
#     _id = serializers.SerializerMethodField(required=False)
#
#     def get__id(self, instance):
#         return str(instance._id)
#
#     class Meta:
#         model = Team
#         fields = ["_id", "name", "node_type", "path", "index"]


class MinimalNodeSerialiizer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    name = serializers.SerializerMethodField()
    node_type = serializers.CharField(max_length=120)

    def get_name(self, instance):
        node = TreeStructure.objects.get(_id=instance._id).get_object()

        return node.name


class TreeStructureWithoutChildrenSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    node_type = serializers.CharField(max_length=48)      
    name = serializers.SerializerMethodField()

    def get_name(self, instance):
        node = TreeStructure.objects.get(_id=instance._id).get_object()

        return node.name

class TreeStructureWithChildrenSerializer(serializers.Serializer):
    _id = ObjectIdField(read_only=True)
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    node_type = serializers.CharField(max_length=48)

    def get_name(self, instance):
        node = TreeStructure.objects.get(_id=instance._id).get_object()

        return node.name

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
        
        self.all_children = TreeStructure.objects.filter(child_condition, role_condition)

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