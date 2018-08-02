from django.test import TestCase
from vpmoapp.models import Team
from vpmoauth.models import MyUser
from vpmoauth import views
from rest_framework.test import APIRequestFactory, force_authenticate
import os

# Create your tests here.
class UserPermissionsTestCase(TestCase):
	""" Tests the GET and POST methods of the UserPermissionsView """
	def setUp(self):
		""" Method called on initialization of test """
		self.view = views.UserPermissionsView.as_view()
		# MyUser Credentials used for the testing
		user_creds = {
			"username": "TestCasetestUser",
			"email": "testcasetestuser@vpmotest.com"
		}
		self.user = MyUser.objects.create(**user_creds)
		# Random password created on each iteration
		self.password = os.urandom(12).encode('hex')
		self.user.set_password(self.password)

		# Team used for testing
		self.team = Team.objects.create(name="testCaseTeam")

		# Creating the request factory
		self.factory = APIRequestFactory()

	def tearDown(self):
		self.user.delete()
		self.team.delete()

	def test_user_permissions(self):
		""" Testing the GET and POST methods of the UserPermissionsView """
		get_url = "/vpmoauth/api/user_perms/?user={}&team={}".format(self.user.id, self.team.id)
		request = self.factory.get(get_url)
		# Authenticating the GET request
		force_authenticate(request, user=self.user)
		response = self.view(request)

		self.assertEqual(response.data, [])


