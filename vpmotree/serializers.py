from rest_framework import serializers
from .models import Team, Project, Deliverable, NodeType


class ProjectSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "start", "project_owner"]


class TeamSerializer(serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Team
        fields = ["_id", "name", "user_linked", "created_at", "updated_at", "user_team"]


class DeliverableSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Deliverable"

    class Meta:
        model = Deliverable
        fields = ["_id", "name", "obj_type", "path", "index"]


class ProjectTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Project"

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "obj_type", "path", "index"]


class TeamTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Team"

    class Meta:
        model = Team
        fields = ["_id", "name", "obj_type", "path", "index"]


class TreeStructureWithoutChildrenSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    path = serializers.CharField(max_length=4048, source="path")
    index = serializers.IntegerField(source="index")
    obj_type = serializers.SerializerMethodField()


    def get_obj_type(self, instance):
        return type(instance).__name__
        

    def get__id(self, instance):
        return str(instance._id)


class TreeStructureWithChildrenSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    path = serializers.CharField(max_length=4048, source="path")
    index = serializers.IntegerField(source="index")
    children = serializers.SerializerMethodField()
    obj_type = serializers.SerializerMethodField()


    def get_obj_type(self, instance):
        return type(instance).__name__


    def get_branch_extensions(self, branch, branch_level):
        """ Takes a branch as input and starts the loop for either the next branches (if they exist) or the leaves """
        next_level = branch_level + 1
        # Finding children on the next level with the current branch._id in the path
        children = filter(lambda x: x["path"].count(',') == next_level and branch["_id"] in x["path"], self.all_children)
        children = sorted(children, key=lambda x: x["index"])
        for child in children:
            child["children"] = self.get_branch_extensions(child, next_level)

        return children


    def get_children(self, instance):
        """ Takes a team as input and returns the Tree it is the root of """
        children = []

        # All objects starting from the current ROOT (Team)
        self.all_children = TreeStructureWithoutChildrenSerializer(TreeStructure.objects.filter(
            path__startswith=","+instance._id), many=True).data
        # Finding the first branches from the root (Projects)
        top_level = 2
        first_branches = filter(lambda x: x["path"]count(",") == top_level, self.all_children)
        first_branches = sorted(first_branches, key=lambda x: x["index"])

        for branch in first_branches:
            branch["children"] = self.get_branch_extensions(branch, top_level)
            children.append(branch)

        return children


    def get__id(self, instance):
        return str(instance._id)
