# from django.shortcuts import render, HttpResponse
# # from django.contrib.auth.models import User, Group
# from django.contrib.auth import authenticate
# from django.contrib.auth import get_user_model
#
# from rest_framework import viewsets
# from rest_framework.authentication import SessionAuthentication, BasicAuthentication
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.authtoken.models import Token
# from rest_framework import status
# from rest_framework.generics import CreateAPIView
# from rest_framework.response import Response
# from rest_framework_jwt.settings import api_settings
# from rest_framework.permissions import AllowAny
# import jwt
# import json
#
# from vpmoapp.serializers import UserSerializer
# from vpmoprj.settings import SECRET_KEY
#
# jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
# jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
#
#
# class CreateUserView(CreateAPIView):
#     # CreateAPIView provide only Post method
#     model = get_user_model()
#     # set permission as AllowAny user to Register
#     permission_classes = (AllowAny,)
#     # queryset = get_user_model().object().all
#     serializer_class = UserSerializer
#
#     # def post(self, request, *args, **kwargs):
#     #     serializer = self.get_serializer(data=request.data)
#     #     if serializer.is_valid(raise_exception=True):
#     #         self.perform_create(serializer)
#     #         headers = self.get_success_headers(serializer.data)
#     #         user = self.model.get(email=serializer.data['email'])
#     #         payload = jwt_payload_handler(user)
#     #         token = jwt_encode_handler(payload)
#     #         return Response(
#     #             token,
#     #             status=status.HTTP_201_CREATED,
#     #             headers=headers
#     #         )
#     #     else:
#     #         return Response(
#     #             status=status.HTTP_400_BAD_REQUEST
#     #         )
#
#
# class LoginUserView(APIView):
#
#     def post(self, request, *args, **kwargs):
#         email = request.data.get('email')
#         password = request.data.get('password')
#
#         user = authenticate(email=email, password=password)
#         if user:
#             payload = jwt_payload_handler(user)
#             token = {
#                 'token': jwt.encode(payload, SECRET_KEY),
#                 'status': 'success'
#                 }
#             return Response(token)
#         else:
#             return Response(
#               {'error': 'Invalid credentials',
#               'status': 'failed'},
#             )
