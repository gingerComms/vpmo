from django.shortcuts import render
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.apps import apps
from rest_framework.permissions import AllowAny

from vpmotree.models import Team, Project, TreeStructure
from vpmoauth.permissions import AssignRolesPermission, RemoveRolesPermission
from vpmoauth.models import MyUser, UserRolePermission, UserRole
from vpmoauth.serializers import *
from vpmoprj.serializers import MinimalNodeSerializer

from rest_framework import generics, permissions, mixins, status, filters
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateAPIView, get_object_or_404

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
import jwt


# Create your views here.

class FavoriteNodesView(APIView):
    """ Endpoint for adding/removing favorite nodes from the user's m2m field """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MinimalNodeSerializer

    def get_node(self, node_id):
        """ Retrieves the node from the given ID """
        try:
            return TreeStructure.objects.get(_id=node_id)
        except TreeStructure.DoesNotExist:
            return None

    def get(self, request):
        return Response(self.serializer_class(request.user.favorite_nodes.all(), many=True).data)

    def put(self, request):
        """ Adds the given node to the user's m2m field """
        data = request.data.copy()
        node = self.get_node(data["node"])

        # Adding the node to the user's favorites
        request.user.favorite_nodes.add(node)
        request.user.save()

        return Response(self.serializer_class(request.user.favorite_nodes.all(), many=True).data)

    def delete(self, request):
        """ Removes the given user from the user's m2m fieild """
        data = request.data.copy()
        node = self.get_node(data["node"])

        # List of nodes the user has in favorites currently
        current_favorites = request.user.favorite_nodes.all().values_list("_id", flat=True)
        # Checking if the input id even exists in the current favorites
        if node._id in current_favorites:
            request.user.favorite_nodes.remove(node)
            request.user.save()
        else:
            return Response({"message": "Node does not exist in user's favorite nodes"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.serializer_class(request.user.favorite_nodes.all(), many=True).data)


class AssignableUsersListView(generics.ListAPIView):
    """ Returns a list of users that can be assigned a role for a given node """
    serializer_class = UserDetailsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("username","email","fullname")

    def get_queryset(self):
        # Fetching the node
        try:
            node = TreeStructure.objects.get(_id=self.kwargs["node_id"])
            node = node.get_object()
        except TreeStructure.DoesNotExist:
            return []

        existing_users = UserRole.get_user_ids_with_perms(node)

        # If node is a Team, return ALL registered users
        if node.node_type == "Team":
            # Because exclude isn't working...
            user_ids = MyUser.objects.all().values_list("_id", flat=True)
            user_ids = filter(lambda x: x not in existing_users, user_ids)
            print(user_ids)
            return MyUser.objects.filter(_id__in=user_ids)
        
        root_users = UserRole.get_user_ids_with_perms(node.get_root())
        root_users = filter(lambda x: x not in existing_users, root_users)
        root_users = MyUser.objects.filter(_id__in=root_users)
        return root_users


class AssignRoleView(APIView):
    permission_classes = (permissions.IsAuthenticated, AssignRolesPermission,)

    def get_object(self):
        try:
            obj = TreeStructure.objects.get(_id=self.request.data["nodeID"])
            obj = obj.get_object()
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
            target_user = MyUser.objects.get(username=request.data["user"])
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
        try:
            node = TreeStructure.objects.get(_id=node_id)
            node = node.get_object()
        except TreeStructure.DoesNotExist:
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
        try:
            node = TreeStructure.objects.get(_id=self.kwargs["node_id"])
            node = node.get_object()
        except TreeStructure.DoesNotExist:
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


class UserUpdateView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # permission_classes = [permissions.AllowAny]
    queryset = get_user_model()
    serializer_class = UserDetailsSerializer
    lookup_field = '_id'

    def partial_update(self, request, _id, *args, **kwargs):
        try:
            user = get_user_model().objects.get(_id = _id)
        except MyUser.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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