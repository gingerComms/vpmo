from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from vpmoapp.models import MyUser
from rest_framework import authentication

class AuthBackend(authentication.BaseAuthentication):
	""" The first backend for Authentication through MyUser
		A MyUser object is returned on successful authentication and None on failure
	"""
	def authenticate(self, request, email=None, password=None):
		# Password is not checked if user object is not found and authentication is denied
		try:
			user = MyUser.objects.get(email=email)
		except MyUser.DoesNotExist:
			return None
		
		# Checks if the password hash for the user object matches the hash of input password
		if user.check_password(password):
			return user
		return None

	def get_user(self, user_id):
		""" Returns the MyUser instance associated with a request's session
			The MyUser instance is then used to validate the user using
			self.get_session_auth_hash()
		"""
		try:
			return MyUser.objects.get(pk=user_id)
		except MyUser.DoesNotExist:
			return None