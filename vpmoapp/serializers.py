from rest_framework.serializers import ModelSerializer
from .models import Team, Project



class ProjectSerializer(ModelSerializer):

    class Meta:
        model = Project
        fields = '__all__'


class TeamSerializer(ModelSerializer):
    # projects = ProjectSerializer(read_only=True, many=True)

    class Meta:
        model = Team
        fields = '__all__'



class TeamTreeSerializer(ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'