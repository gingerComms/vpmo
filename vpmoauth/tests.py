from django.test import TestCase
from django.shortcuts import *
from vpmoapp.models import Team
from vpmoauth.models import MyUser
from vpmoauth import views
from rest_framework.test import APIRequestFactory, force_authenticate
import os
import json
import binascii

# Create your tests here.

# UNKNOWN ISSUE WITH TESTS DUE TO GUARDIAN + MONGODB
# 	TESTS RUN PROPERLY ONLY ON EVERY SECOND ATTEMPT. IF ONE RUN FAILS WITH EXC, ALWAYS TRY TO RUN THE TESTS AGAIN


class UserPermissionsTestCase(TestCase):
	""" Tests the GET and POST methods of the UserPermissionsView """
	def setUp(self):
		""" Method called on initialization of test """
		self.view = views.UserPermissionsView.as_view()
		# MyUser Credentials used for the testing
		user_creds = {
			"username": "TestUser",
			"email": "TestUser@vpmotest.com"
		}
		self.user = MyUser.objects.create(**user_creds)
		# Random password created on each iteration
		self.password = binascii.hexlify(os.urandom(12))
		self.user.set_password(self.password)

		# Team used for testing
		self.team = Team.objects.create(name="testCaseTeam")

		# Creating the request factory
		self.factory = APIRequestFactory()

	def tearDown(self):
		self.user.delete()
		self.team.delete()


	def create_get_request(self, url):
		""" Creates the get request for the actual test """
		get_url = url+"?user={}&team={}".format(self.user.id, self.team.id)
		request = self.factory.get(get_url)
		# Authenticating the GET request
		force_authenticate(request, user=self.user)
		response = self.view(request)
		return response


	def create_post_request(self, url, post_data):
		""" Creates the post request for the actual test """
		request = self.factory.post(url, json.dumps(post_data), content_type='application/json')
		force_authenticate(request, user=self.user)
		response = self.view(request)
		return response


	def test_user_permissions(self):
		""" Testing the GET and POST methods of the UserPermissionsView """
		url = reverse("user-perms")
		
		# Doing the first request with no permissions
		get_resp = self.create_get_request(url)
		self.assertEqual(get_resp.data, [])

		# Doing the second request to add "read_obj" permissions
		post_data = {
			"user": self.user.id,
			"team": self.team.id,
			"permission": "read_obj"
		}
		post_resp = self.create_post_request(url, post_data)
		self.assertEqual(post_resp.data, ["read_obj"])

		# Doing the third get_request to confirm that permissions were added
		get_resp = self.create_get_request(url)
		self.assertEqual(get_resp.data, ["read_obj"])





