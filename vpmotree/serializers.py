from rest_framework import serializers
from .models import Team, Project, Deliverable


class ProjectSerializer(serializers.ModelSerializer):
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "start", "project_owner", "team", "parent_project"]


class TeamSerializer(serializers.ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    class Meta:
        model = Team
        fields = ["_id", "name", "user_linked", "created_at", "updated_at", "userTeam"]


class DeliverableSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)
    children = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Deliverable"

    def get_children(self, instance):
        """ Gets all children (can only have topic children) """
        data = DeliverableSerializer(Deliverable.objects.filter(parent_topic=instance), many=True).data
        # NOTE - To increase this to more models, you'll be looping through a list of all those other models
        #   And added the XSerializer(TopicModel.objects.filter(parent_topic=instance, many=True)).data to the data list that is returned here
        return data

    class Meta:
        model = Deliverable
        fields = ["_id", "name", "obj_type", "path", "index", "children"]


class ProjectTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    children = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Project"

    def get_children(self, instance):
        """ Gets all children projects and topic, serializes them and returns """
        data = []
        data += ProjectTreeSerializer(Project.objects.filter(parent_project=instance), many=True).data
        data += DeliverableSerializer(Deliverable.objects.filter(project=instance), many=True).data

        data = sorted(data, key=lambda x: x["index"])
        return data

    class Meta:
        model = Project
        fields = ["_id", "name", "description", "obj_type", "children", "path", "index"]


class TeamTreeSerializer(serializers.ModelSerializer):
    obj_type = serializers.SerializerMethodField(required=False)
    projects = serializers.SerializerMethodField(required=False)
    _id = serializers.SerializerMethodField(required=False)

    def get__id(self, instance):
        return str(instance._id)

    def get_obj_type(self, instance):
        return "Team"

    def get_projects(self, instance):
        """ Returns all children projects """
        data = ProjectTreeSerializer(Project.objects.filter(team=instance), many=True).data
        data = sorted(data, key=lambda x: x["index"])
        return data

    class Meta:
        model = Team
        fields = ["_id", "name", "obj_type", "projects", "path", "index"]