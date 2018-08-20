from django.test import TestCase
from django.test import Client
from vpmoapp.models import Team, Project, Deliverable
from vpmoauth.models import MyUser
import test_addons
from vpmoapp import views
from django.shortcuts import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APIRequestFactory, force_authenticate
import os, json
import binascii
from copy import copy

# Create your tests here.


class ModelTestCase(test_addons.MongoTestCase):
    # A MongoTestCase needs this argument to use the test database
    allow_database_queries = True

    # creating a song in setup to run multiple tests with one object
    def setUp(self):
        self.old_count = MyUser.objects.count()
        self.object = MyUser.objects.create(email="ali@test.com", username="AliRad")

    # deletion after tests are complete
    def tearDown(self):
        self.object.delete()

    # basic count test
    def test_model_can_create(self):
        new_count = MyUser.objects.count()
        self.assertNotEqual(self.old_count, new_count)


    """ The following two tests are included to ensure django ids and pks are not interfered in the djongo compiling. See full doc for more on my experience with this """
    def test_model_has_id(self):
        self.assertIsNotNone(self.object.id)

    def test_model_has_pk(self):
        self.assertIsNotNone(self.object.pk)


class TeamPermissionsTestCase(TestCase):
    """ Tests for the FilteredTeamsView """

    def setUp(self):
        """ Creating the test user and the test team """
        self.view = views.FilteredTeamsView.as_view()
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
        self.team_with_perms = Team.objects.create(name="testCaseTeam")
        # A random team to confirm we only get the team with permissions in the GET request
        self.team_without_perms = Team.objects.create(name="RandTeam")

        # Creating the request factory
        self.factory = APIRequestFactory()


    def tearDown(self):
        self.user.delete()
        self.team_with_perms.delete()
        self.team_without_perms.delete()


    def test_filtered_team_view(self):
        url  = reverse("filtered_teams")

        # Giving perms to one Team to user
        assign_perm("read_obj", self.user, self.team_with_perms)

        # GET on url to confirm we only get the team with the permissions
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        response = self.view(request)
        
        self.assertEqual(response.data, [{"id": 1, "name": "testCaseTeam"}])


class TreeStructureTestCase(TestCase):
    """ Tests the TeamTreeView for correct inherit structures """
    client = Client()

    def setUp(self):
        """ Creates the models required to test the tree structure """
        self.view = views.TeamTreeView.as_view()
        # MyUser Credentials used for the testing
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "email2": "test2@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
        # Random password created on each iteration
        self.password = binascii.hexlify(os.urandom(12))
        self.user.set_password(self.password)
        self.user.save()

        self.team = Team.objects.create(name="Test Team")
        self.team.save()

        self.project = Project.objects.create(projectname="Test Proj", team=self.team)
        self.project.save()

        self.project_2 = Project.objects.create(projectname="Test Proj 2", team=self.team)
        self.project_2.save()

        self.topic = Deliverable.objects.create(name="Test Del", project=self.project)
        self.topic.save()

        # Creating the request factory
        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")

    def tearDown(self):
        self.user.delete()
        self.project.delete()
        self.project_2.delete()
        self.topic.delete()

    def test_tree_structure_get(self):
        """ Makes the necessary requests and asserts to test the GET TeamTreeView """
        url = reverse("team_tree_view", kwargs={"team_id": str(self.team._id)})
        # GET on url to get the current tree structure
        first_response = self.client.get(url).json()

        self.topic.project = self.project_2
        self.topic.save()

        second_response = self.client.get(url).json()

        self.assertNotEqual(first_response, second_response)


    def test_tree_structure_post(self):
        """ Makes the necessary requests and asserts to test the POST TeamTreeView """
        url = reverse("team_tree_view", kwargs={"team_id": str(self.team._id)})
        # GET on url to get the current tree structure
        first_response = self.client.get(url).json()

        new_d = copy(first_response)
        proj = new_d["projects"].pop(1)
        new_d["projects"].insert(0, proj)

        second_response = self.client.put(url, new_d).json()

        self.assertNotEqual(first_response, second_response)
