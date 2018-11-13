from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class TwilioTokenView(APIView):
	""" Generates and returns a Twilio token for authenticated user """
	permission_classes = (IsAuthenticated,)

	def get(self, request):
		pass