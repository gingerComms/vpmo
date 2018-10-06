from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from rest_framework.permissions import AllowAny

from vpmotree.models import Team, Project
from vpmoauth.permissions import AssignPermissionsPermission
from vpmoauth.models import MyUser
from vpmoauth.serializers import *

from rest_framework import generics, permissions, mixins
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from guardian import shortcuts

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
import jwt



# Create your views here.

class UserPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated,]
    # permission_classes = [AllowAny]
    def get(self, request):
        """ Returns a list of permissions held by the input User for the input Team """
        user = MyUser.objects.get(_id=request.query_params.get("user", None))
        team = Team.objects.get(_id=request.query_params.get("team", None))

        return Response(shortcuts.get_perms(user, team))

    def post(self, request):
        """ Adds input permission for input team to input user """
        assert request.data.get("permission", None) in ["read_obj", "create_obj", "delete_obj", "update_obj"]

        user = MyUser.objects.get(_id=request.data.get("user", None))
        team = Team.objects.get(_id=request.data.get("team", None))

        shortcuts.assign_perm(request.data["permission"], user, team)

        return Response(shortcuts.get_perms(user, team))


class AssignRoleView(generics.RetrieveUpdateAPIView):
    permission_classes = (permission.IsAuthenticated, AssignRolesPermission,)
    lookup_field = "_id"
    valid_roles = {
        "team": ["team_member", "team_lead", "team_admin"],
        "project": ["project_admin", "project_contributor", "project_viewer"]
    }

    def get_object(self):
        """ Returns the model set by node_id with the input _id """
        node = globals[self.request.query_params["node_type"]]
        try:
            obj = node.objects.get(_id=self.kwargs["node_id"])
        except node.DoesNotExist:
            return None

        return opj

    def put(self, request):
        """ Assigns the permissions related to the role for the input node
            to the input user if the request user has permissions to assign permissions
            for the input node
        """
        # Reading data from the request
        role = request.query_params["role"]
        try:
            target_user = MyUser.objects.get(_id=request.query_params["user"])
        except MyUser.DoesNotExist:
            return Response({"message": "Target User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        node = self.get_object()
        if not node:
            return Response({"message": "Node does not exist"}, status=status.HTTP_404_NOT_FOUND)




class AllUserView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = AllUsersSerializer
    permission_classes = [permissions.IsAuthenticated,]
    # permission_classes = [AllowAny]


class UserUpdateView(mixins.UpdateModelMixin, generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = get_user_model().objects.all()
    serializer_class = UserDetailsSerializer
    lookup_field = '_id'

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class UserDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = get_user_model().objects.all()
    serializer_class = UserDetailsSerializer
    lookup_field = '_id'
    # lookup_url_kwarg = 'user'


class CreateUserView(generics.CreateAPIView):
    # CreateAPIView provide only Post method
    model = get_user_model()
    # set permission as AllowAny user to Register
    permission_classes = (permissions.AllowAny,)
    # queryset = get_user_model().object().all
    serializer_class = UserDeserializer


class LoginUserView(APIView):
    permission_classes = (permissions.AllowAny,)
    # serializer_class = UserSerializer
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(email=email, password=password)
        if user:
            currentUser = get_user_model().objects.get(email=email)
            payload = jwt_payload_handler(user)
            payload["user_id"] = str(payload["user_id"])
            token = {
                'token': jwt.encode(payload, settings.SECRET_KEY),
                'status': 'success',
                'fullname': currentUser.fullname,
                'username': currentUser.username,
                'email': currentUser.email,
                '_id': str(currentUser._id),
                }
            return Response(token)
        else:
            return Response(
              {'error': 'Invalid credentials',
              'status': 'failed'},
            )


def profile(request):
    arg = {'user': request.user}
    return Response(arg)