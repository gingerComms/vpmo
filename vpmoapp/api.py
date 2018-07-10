from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    RetrieveAPIView,
    DestroyAPIView)
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
from .models import Team, Project
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_jwt.settings import api_settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from vpmoprj.settings import SECRET_KEY

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
import jwt


class AllTeamsView(ListAPIView):
    serializer_class = TeamSerializer
    queryset = Team.objects.all()


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