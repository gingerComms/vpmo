from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.apps import apps
from rest_framework.permissions import AllowAny

from vpmotree.models import Team, Project, TreeStructure
from vpmoauth.permissions import AssignRolesPermission, RemoveRolesPermission
from vpmoauth.models import MyUser, UserRolePermission, UserRole
from vpmoauth.serializers import *

from rest_framework import generics, permissions, mixins, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from guardian import shortcuts

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
import jwt



# Create your views here.

class AssignableUsersListView(generics.ListAPIView):
    """ Returns a list of users that can be assigned a role for a given node """
    serializer_class = UserDetailsSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        model = apps.get_model("vpmotree", self.request.query_params["nodeType"])
        # Fetching the node
        try:
            node = model.objects.get(_id=self.kwargs["node_id"])
        except model.DoesNotExist:
            return []

        existing_users = UserRole.get_user_ids_with_perms(node)

        # If node is a Team, return ALL registered users
        if node.node_type == "Team":
            return MyUser.objects.all().exclude(_id__in=existing_users)
        
        root_users = UserRole.get_user_ids_with_perms(node.get_parent())
        root_users = filter(lambda x: x not in existing_users, root_users)
        root_users = MyUser.objects.filter(_id__in=root_users)
        return root_users


class AssignRoleView(APIView):
    permission_classes = (permissions.IsAuthenticated, AssignRolesPermission,)

    def get_object(self):
        node = apps.get_model("vpmotree", self.request.data["nodeType"])
        try:
            obj = node.objects.get(_id=self.request.data["nodeID"])
        except node.DoesNotExist:
            return None

        perms = self.check_object_permissions(self.request, obj)
        return obj


    def put(self, request):
        """ Assigns the permissions related to the role for the input node
            to the input user if the request user has permissions to assign permissions
            for the input node
        """
        # Reading data from the request
        role = request.data.get("role")
        try:
            target_user = MyUser.objects.get(_id=request.data["userID"])
        except MyUser.DoesNotExist:
            return Response({"message": "Target User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        node = self.get_object()
        if not node:
            return Response({"message": "Node does not exist"}, status=status.HTTP_404_NOT_FOUND)

        target_user.assign_role(role, node)

        data = UserDetailsSerializer(target_user).data
        data["role"] = target_user.get_role(node).role_name

        return Response(data)


class UserNodePermissionsView(APIView):
    """ Returns the permissions a user has for the current node """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, node_id):
        model = apps.get_model('vpmotree', request.query_params["nodeType"])
        try:
            node = model.objects.get(_id=node_id)
        except model.DoesNotExist:
            return Response({"message": "Tree structure not found."}, status=status.HTTP_404_NOT_FOUND)

        permissions = request.user.get_permissions(node)
        
        user_role = request.user.get_role(node)
        
        return Response({
            "permissions": permissions,
            "role": user_role.role_name if user_role else None,
            "_id": str(request.user._id)
        })


class RemoveUserRoleView(generics.DestroyAPIView):
    """ Removes the role a user has for a particular node """
    permission_classes = (permissions.IsAuthenticated, RemoveRolesPermission)

    def get_object(self):
        model = apps.get_model("vpmotree", self.request.query_params["nodeType"])
        try:
            node = model.objects.get(_id=self.kwargs["node_id"])
        except model.DoesNotExist:
            return None

        perms = self.check_object_permissions(self.request, node)
        return node

    def get_user(self):
        try:
            user = MyUser.objects.get(_id=self.request.query_params["user"])
        except MyUser.DoesNotExist:
            return None
        return user

    def delete(self, request, node_id):
        node = self.get_object()
        if node is None:
            return Response({"message": "Node not found"}, status=status.HTTP_404_NOT_FOUND)
        user = self.get_user()
        if user is None:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        role = request.query_params.get("role", None)
        user.remove_role(node)

        return Response("Success")


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