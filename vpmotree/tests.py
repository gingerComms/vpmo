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
from create_base_permissions import create_base_permissions

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


class ProjectUpdateTestCase(TestCase):
    """ TestCase for testing the Project RetreiveUpdateView """
    client = Client()

    def setUp(self):
        self.view = views.UpdateProjectView

        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)

        self.project = Project(name="Test Proj", project_owner=self.user)
        self.project.save()

        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")


    def test_update(self):
        url = reverse("update_project", kwargs={"_id": str(self.project._id)})

        data = {
            "content": "Hello there!"
        }

        response = self.client.patch(url, json.dumps(data), content_type='application/json').json()

        print(response)

        self.assertEqual(response["content"], "Hello there!")


class NodePermissionsViewTestCase(TestCase):
    """ Test for the nodepermissions retrieve api view """
    client = Client()

    def setUp(self):
        self.view = views.NodePermissionsView

        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)

        self.project = Project(name="Test Proj", project_owner=self.user)
        self.project.save()

        assign_perm("read_obj", self.user, self.project)

        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")


    def test_get(self):
        url = reverse("node_permissions", kwargs={"node_id": self.project._id})+"?nodeType=Project"

        response = self.client.get(url).json()

        print(response)


class ReadNodeListFilterTestcase(TestCase):
    client = Client()

    def setUp(self):
        """ Creates the models required to test the tree structure """
        create_base_permissions()
        self.view = views.AllProjectsView.as_view()
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

        self.team = Team(name="Test Team", user_team="Blah")
        self.team.save()

        self.team_2 = Team(name="Test Team 2", user_team="BlahBlah")
        self.team_2.save()

        self.user.assign_role("team_admin", self.team)
        self.user.save()

        self.project = Project(name="Test Proj", index=0, path=",{},".format(self.team._id))
        self.project.save()

        self.project_2 = Project(name="Test Proj 2", index=0, path=",{},".format(self.team_2._id))

        self.topic = Deliverable(name="Test Topic", index=0, path="{}{},".format(self.project.path, self.project._id))
        self.topic.save()

        self.topic_2 = Deliverable(name="Test Topic 2", index=0, path="{}{},".format(self.project_2.path, self.project_2._id))
        self.topic_2.save()

        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")


    def test_filter(self):
        # Project Test
        url = reverse("all_nodes")+"?nodeType=Project&parentNodeID="+str(self.team._id)

        response = self.client.get(url).json()

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["_id"], str(self.project._id))

        # Topic Test (Deliverable)
        url = reverse("all_nodes")+"?nodeType=Deliverable&parentNodeID="+str(self.project._id)

        response = self.client.get(url).json()

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["_id"], str(self.topic._id))


class TaskTestCase(TestCase):
    client = Client()

    def setUp(self):
        create_base_permissions()
        project_admin_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.project_admin = MyUser.objects.create(**project_admin_creds)

        project_contributor_creds = {
            "username": "TestUser2",
            "email": "TestUser2@vpmotest.com",
            "fullname": "Test2 User"
        }
        self.project_contributor = MyUser.objects.create(**project_contributor_creds)

        self.project = Project(name="Test Proj", project_owner=self.project_admin)
        self.project.save()

        self.project_admin.assign_role("project_admin", self.project)
        self.project_contributor.assign_role("project_contributor", self.project)

        self.client.force_login(self.project_admin)

    def test_task_create(self):
        """ Tests the task creation POST endpoint """
        url = reverse("vpmotree:create_task")+"?nodeType=Project"

        data = {
            "node": self.project._id,
            "title": "Test Task",
            "status": "NEW",
            "due_date": "2015-12-16"
        }

        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)