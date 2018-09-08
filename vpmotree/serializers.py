from rest_framework import serializers
from .models import Team, Project, Deliverable, TreeStructure
from django.apps import apps

class ProjectSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "start", "project_owner", "path", "index"]


class TeamSerializer(serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Team
        fields = ["_id", "name", "user_linked", "created_at", "updated_at", "user_team"]


class DeliverableSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Deliverable
        fields = ["_id", "name", "node_type", "path", "index"]


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


class TreeStructureWithoutChildrenSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    node_type = serializers.CharField(max_length=48)      
    name = serializers.SerializerMethodField()

    def get__id(self, instance):
        return str(instance._id)

    def get_name(self, instance):
        model = apps.get_model('vpmotree', instance.node_type)
        name = model.objects.get(treestructure_ptr_id=instance).name
        return name

class TreeStructureWithChildrenSerializer(serializers.Serializer):
    _id = serializers.SerializerMethodField()
    path = serializers.CharField(max_length=4048)
    index = serializers.IntegerField()
    name = serializers.CharField(max_length=150)
    children = serializers.SerializerMethodField()
    node_type = serializers.CharField(max_length=48)


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

        if instance.node_type == "Team":
            # All objects starting from the current ROOT (Team)
            self.all_children = TreeStructureWithoutChildrenSerializer(TreeStructure.objects.filter(
                path__startswith=","+str(instance._id)).filter(node_type="Project"), many=True).data
            # Finding the first branches from the root (Projects)
            top_level = 2
        else:
            if instance.node_type == "Project":
                self.all_children = TreeStructureWithoutChildrenSerializer(TreeStructure.objects.filter(
                    path__contains= str(instance._id)), many=True).data
                top_level = instance.path.count(",") + 1

        first_branches = filter(lambda x: x["path"].count(",") == top_level, self.all_children)
        first_branches = sorted(first_branches, key=lambda x: x["index"])

        for branch in first_branches:
            branch["children"] = self.get_branch_extensions(branch, top_level)
            children.append(branch)

        return children


    def get__id(self, instance):
        return str(instance._id)
