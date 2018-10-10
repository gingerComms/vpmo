from django.test import TestCase
from django.shortcuts import *
from vpmotree.models import Team, Project, Deliverable
from vpmoauth.models import MyUser
from vpmoauth import views
from rest_framework.test import APIRequestFactory, force_authenticate
import os
import json
import binascii
from guardian import shortcuts

# Create your tests here.

# UNKNOWN ISSUE WITH TESTS DUE TO GUARDIAN + MONGODB
# 	TESTS RUN PROPERLY ONLY ON EVERY SECOND ATTEMPT. IF ONE RUN FAILS WITH EXC, ALWAYS TRY TO RUN THE TESTS AGAIN


class UserRolesTestCase(TestCase):
	""" Tests that all of the user's role-based methods are working correctly """
	def setUp(self):
		user_creds = {
			"username": "TestUser",
			"email": "TestUser@vpmotest.com"
		}
		self.user = MyUser.objects.create(**user_creds)
		# Random password created on each iteration
		self.password = binascii.hexlify(os.urandom(12))
		self.user.set_password(self.password)
		self.user.create_user_team()
		self.user.save()

		self.team = Team.objects.first()

		self.project = Project(project_owner=self.user, name="Proj")
		self.project.save()
		self.project.path = ",{},".format(str(self.team._id))
		self.project.save()

		self.topic = Deliverable(name="Topic")
		self.topic.save()
		self.topic.path = "{},".format(self.project.path)
		self.topic.save()

	def test_roles(self):
		self.assertEqual(self.user.get_role(self.team), "team_admin")


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
		self.user.save()

		# TODO: Add user.create_team call, create a project under that team, check if user has permission to that project using
		# 	Project.user.has_permission(user, "read_obj")



