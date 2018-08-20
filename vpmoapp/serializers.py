from rest_framework import serializers
from .models import Team, Project, Deliverable



class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'


class TeamSerializer(serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)

    class Meta:
        model = Team
        fields = '__all__'


class DeliverableSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField()

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Deliverable"

    class Meta:
        model = Deliverable
        fields = ["_id", "name", "obj_type", "path"]


class ProjectTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    children = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField()

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Project"

    def get_children(self, instance):
        """ Gets all children projects and topic, serializes them and returns """
        data = []
        data += ProjectTreeSerializer(Project.objects.filter(parent_project=instance), many=True).data
        data += DeliverableSerializer(Deliverable.objects.filter(project=instance), many=True).data

        return data

    class Meta:
        model = Project
        fields = ["_id", "projectname", "description", "obj_type", "children", "path"]


class TeamTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    projects = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField()

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Team"

    def get_projects(self, instance):
        """ Returns all children projects """
        return ProjectTreeSerializer(Project.objects.filter(team=instance), many=True).data

    class Meta:
        model = Team
        fields = ["_id", "name", "obj_type", "projects", "path"]