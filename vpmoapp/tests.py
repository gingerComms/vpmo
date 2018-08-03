from django.test import TestCase
from vpmoapp.models import Team
from vpmoauth.models import MyUser
import test_addons
from vpmoapp import views
from django.shortcuts import reverse
from guardian.shortcuts import assign_perm
from rest_framework.test import APIRequestFactory, force_authenticate
import os, json
import binascii

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