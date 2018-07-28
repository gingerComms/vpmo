from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    RetrieveAPIView,
    DestroyAPIView,
    RetrieveUpdateAPIView)
from rest_framework.mixins import (
    UpdateModelMixin,
    DestroyModelMixin
    )
from django.contrib.auth import authenticate

from .serializers import (
        TeamSerializer,
        UserDeserializer,
        ProjectSerializer,
        AllUsersSerializer,
        UserDetailsSerializer
        )
from .models import Team, Project, MyUser
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_jwt.settings import api_settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework import filters
from vpmoprj.settings import SECRET_KEY
from vpmoapp.permissions import TeamPermissions
from vpmoapp.filters import TeamListFilter
from guardian import shortcuts

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
import jwt


class AllTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, TeamPermissions]
    queryset = Team.objects.all()
    filter_backends = (TeamListFilter,)


class UserPermissionsView(APIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    def get(self, request):
        """ Returns a list of permissions held by the input User for the input Team """
        user = MyUser.objects.get(id=request.query_params.get("user", None))
        team = Team.objects.get(id=request.query_params.get("team", None))

        return Response(shortcuts.get_perms(user, team))

    def post(self, request):
        """ Adds input permission for input team to input user """
        assert request.data.get("permission", None) in ["read_obj", "contribute_obj", "created_obj"]

        user = MyUser.objects.get(id=request.data.get("user", None))
        team = Team.objects.get(id=request.data.get("team", None))

        shortcuts.assign_perm(request.data["permission"], user, team)

        return Response(shortcuts.get_perms(user, team))



class AllProjectsView(ListAPIView):
    serializer_class = ProjectSerializer
    # permission_classes = [AllowAny]
    queryset = Project.objects.all()


class AllUserView(ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = AllUsersSerializer
    permission_classes = (AllowAny,)


class UserUpdateView(UpdateModelMixin, RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = get_user_model().objects.filter(id__gte=0)
    serializer_class = UserDetailsSerializer
    lookup_field = 'id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class UserDetailsView(RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = get_user_model().objects.all()
    serializer_class = UserDetailsSerializer
    lookup_field = 'id'
    # lookup_url_kwarg = 'user'



# class CreateUserView(CreateAPIView):
#     # CreateAPIView provide only Post method
#     model = get_user_model()
#     # set permission as AllowAny user to Register
#     permission_classes = (AllowAny,)
#     # queryset = get_user_model().object().all
#     serializer_class = UserSerializer


class CreateUserView(CreateAPIView):
    # CreateAPIView provide only Post method
    model = get_user_model()
    # set permission as AllowAny user to Register
    permission_classes = (AllowAny,)
    # queryset = get_user_model().object().all
    serializer_class = UserDeserializer


class LoginUserView(APIView):
    permission_classes = (AllowAny,)
    # serializer_class = UserSerializer
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(email=email, password=password)
        if user:
            currentUser = get_user_model().objects.get(email=email)
            payload = jwt_payload_handler(user)
            token = {
                'token': jwt.encode(payload, SECRET_KEY),
                'status': 'success',
                'fullname': currentUser.fullname,
                'username': currentUser.username,
                'email': currentUser.email,
                'id': currentUser.id,
                }
            return Response(token)
        else:
            return Response(
              {'error': 'Invalid credentials',
              'status': 'failed'},
            )


class CreateProjectView(CreateAPIView):
    model = Project
    serializer_class = ProjectSerializer
    permission_classes = (AllowAny,)