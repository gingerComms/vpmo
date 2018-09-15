from django.test import TestCase
from django.test import Client
from vpmotree.models import Team, Project, Deliverable
from vpmoauth.models import MyUser
import test_addons
from vpmotree import views
from django.shortcuts import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APIRequestFactory, force_authenticate
import os, json
import binascii
from copy import copy
from vpmotree import serializers

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
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
        # Random password created on each iteration
        self.password = binascii.hexlify(os.urandom(12))
        self.user.set_password(self.password)
        self.user.save()

        self.team = Team(name="Test Team")
        self.team.save()

        self.project = Project(name="Test Proj", index=0, path=",{},".format(self.team._id))
        self.project.save()

        self.project_2 = Project(name="Test Proj 2", index=1, path=",{},".format(self.team._id))
        self.project_2.save()

        self.project_3 = Project(name="Test Proj 3", index=0, path=self.project.path+str(self.project._id)+",")
        self.project_3.save()

        self.topic = Deliverable(name="Test Del", path=self.project.path+str(self.project._id)+",")
        self.topic.save()
        #print(self.project.path, self.topic.path)

        # Creating the request factory
        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")

    def tearDown(self):
        self.user.delete()
        self.team.delete()
        self.project.delete()
        self.topic.delete()

    def test_tree_structure_get(self):
        """ Makes the necessary requests and asserts to test the GET TeamTreeView """
        url = reverse("team_tree_view", kwargs={"team_id": str(self.team._id)})
        # GET on url to get the current tree structure
        response = self.client.get(url).json()

        expected_response = serializers.TreeStructureWithChildrenSerializer(self.team).data
        self.assertEqual(response, expected_response)


    def test_tree_structure_put(self):
        """ Makes the necessary requests and asserts to test the POST TeamTreeView """
        url = reverse("team_tree_view", kwargs={"team_id": str(self.team._id)})
        # GET on url to get the current tree structure
        first_response = self.client.get(url).json()
        print(json.dumps(first_response, indent=2))

        # Creating the input for the API put
        project_object = serializers.TreeStructureWithoutChildrenSerializer(self.project).data
        project_2_object = serializers.TreeStructureWithoutChildrenSerializer(self.project_2).data
        project_object["index"] += 1
        project_object["path"] = self.project_2.path+str(self.project_2._id)+","
        project_2_object["index"] -= 1

        nodes = [project_object, project_2_object]

        second_response = self.client.put(url, json.dumps(nodes), content_type='application/json').json()
        print(json.dumps(second_response, indent=2))

        self.assertTrue(second_response["children"], msg="PUT response does not have any children")
        if second_response["children"]:
        	self.assertTrue(second_response["children"][0]["children"], msg="LEAF Level children not present in PUT response")
