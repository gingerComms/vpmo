from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from vpmoapp.models import MyUser
from rest_framework import authentication

class AuthBackend(authentication.BaseAuthentication):
	""" Used to authenticate users i.e. Login """
	def authenticate(self, request, email=None, password=None):
		print(email, password)
		try:
			user = MyUser.objects.get(email=email)
		except MyUser.DoesNotExist:
			return None
		
		if user.check_password(password):
			return user
		return None

	def get_user(self, user_id):
		""" Returns user that has pk == user_id """
		try:
			return MyUser.objects.get(pk=user_id)
		except MyUser.DoesNotExist:
			return None