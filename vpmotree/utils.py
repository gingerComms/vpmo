from .models import TreeStructure, Team


def get_team(request):
    data = request.data
    data