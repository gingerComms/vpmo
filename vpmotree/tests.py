from django.test import TestCase, Client
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

class TeamTestCase(TestCase):
    """ Tests related to Teams """
    client = Client()

    def setUp(self):
        """ Creating the test user and the test team """
        self.view = views.FilteredTeamsView.as_view()
        # MyUser Credentials used for the testing
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
        
        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")

    def tearDown(self):
        self.user.delete()

    def test_team_create(self):
        """ Tests the create team view """
        url = reverse("vpmotree:create_team")
        data = {
            "name": "Test Team"
        }
        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)

    """ - NEEDS TO BE REWRITTEN
    def test_filtered_team_view(self):
        url  = reverse("vpmotree:filtered_teams")

        # Giving perms to one Team to user
        assign_perm("read_obj", self.user, self.team_with_perms)

        # GET on url to confirm we only get the team with the permissions
        request = self.factory.get(url)
        force_authenticate(request, user=self.user)
        response = self.view(request)
        
        self.assertEqual(response.data, [{"id": 1, "name": "testCaseTeam"}])
    """


class TreeStructureTestCase(TestCase):
    """ Tests the TeamTreeView for correct inherit structures
        NOTE - NEEDS TO BE REWRITTEN
    """
    client = Client()

    def setUp(self):
        """ Creates the models required to test the tree structure """
        # MyUser Credentials used for the testing
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
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

    def test_node_parent_get(self):
        team_url = reverse("vpmotree:node_parents", kwargs={"nodeID": str(self.team._id)})
        proj_url = reverse("vpmotree:node_parents", kwargs={"nodeID": str(self.project._id)})
        topic_url = reverse("vpmotree:node_parents", kwargs={"nodeID": str(self.topic._id)})

        team_r = self.client.get(team_url)
        proj_r = self.client.get(proj_url)
        topic_r = self.client.get(topic_url)

        # Asserting that the requests went through without exception
        self.assertEqual(team_r.status_code, 200)
        self.assertEqual(proj_r.status_code, 200)
        self.assertEqual(topic_r.status_code, 200)

        # Asserting that the returned response had all required nodes
        self.assertEqual(len(team_r.json()), 1)
        self.assertEqual(len(proj_r.json()), 2)
        self.assertEqual(len(topic_r.json()), 3)


    def test_tree_structure_get(self):
        """ Makes the necessary requests and asserts to test the GET TeamTreeView """
        url = reverse("vpmotree:team_tree_view", kwargs={"team_id": str(self.team._id)})
        # GET on url to get the current tree structure
        response = self.client.get(url).json()

        expected_response = serializers.TreeStructureWithChildrenSerializer(self.team).data
        self.assertEqual(response, expected_response)


    def test_tree_structure_put(self):
        """ Makes the necessary requests and asserts to test the POST TeamTreeView """
        url = reverse("vpmotree:team_tree_view", kwargs={"team_id": str(self.team._id)})
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


class NodeRetrieveUpdateTestCase(TestCase):
    """ TestCase for testing the Node RetreiveUpdateView """
    client = Client()

    def setUp(self):
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)

        self.project = Project(name="Test Proj", project_owner=self.user)
        self.project.save()

        logged_in = self.client.force_login(self.user, backend="vpmoauth.auth_backend.AuthBackend")

        self.url = reverse("vpmotree:node_retrieve_update", kwargs={"nodeID": str(self.project._id)})


    def test_update(self):
        data = {
            "content": "Hello there!"
        }

        response = self.client.patch(self.url, json.dumps(data), content_type='application/json').json()

        self.assertEqual(response["content"], "Hello there!")


    def test_retrieve(self):
        r = self.client.get(self.url)

        self.assertEqual(r.status_code, 200)


class NodePermissionsViewTestCase(TestCase):
    """ Test for the nodepermissions retrieve api view
        NOTE - Currently using guardian - needs to be modified to use UserRolePermissions instead
    """
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
        url = reverse("vpmotree:node_permissions", kwargs={"node_id": self.project._id})+"?nodeType=Project"

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
        url = reverse("vpmotree:all_nodes")+"?nodeType=Project&parentNodeID="+str(self.team._id)

        response = self.client.get(url).json()

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["_id"], str(self.project._id))

        # Topic Test (Deliverable)
        url = reverse("vpmotree:all_nodes")+"?nodeType=Deliverable&parentNodeID="+str(self.project._id)

        response = self.client.get(url).json()

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["_id"], str(self.topic._id))


class NodeCreationTestCase(TestCase):
    """ Tests creation of Projects and Topics """
    client = Client()

    def setUp(self):
        create_base_permissions()
        user_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)

        self.team = Team(name="Test Team", user_team="Blah")
        self.team.save()

        self.user.assign_role("team_admin", self.team)
        self.user.save()

        self.client.force_login(self.user)

    def test_project_creation(self):
        url = reverse("vpmotree:create_node", kwargs={"nodeType": "Project"})

        data = {
            "name": "TestProj",
            "description": "Rand",
            "start": "2018-10-07",
            "parentID": str(self.team._id)
        }

        print(data)

        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)

        return r.json()


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

    def test_task_assignee_update(self):
        self.test_task_create()

        url = reverse("vpmotree:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)

        data = {
            "assignee": str(self.project_admin.username),
            "_id": str(self.task["_id"])
        }

        r = self.client.put(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(str(r.json()["assignee"]["_id"]), str(self.project_admin._id))
        self.assertEqual(r.status_code, 200)

    def test_task_create(self):
        """ Tests the task creation POST endpoint """
        url = reverse("vpmotree:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)

        data = {
            "title": "Test Task",
            "status": "NEW",
            "due_date": "2018-10-07T18:30:00.000Z",
            "node": str(self.project._id)
        }

        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)
        self.task = r.json()

    def test_assignable_task_users(self):
        """ Tests the GET list view for assignable task users """
        self.test_task_create()
        url = reverse("vpmotree:assignable_task_users", kwargs={"nodeID": str(self.project._id)})+"?nodeType=Project"

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)


    def test_assigned_tasks_list(self):
        """ Tests the list method for tasks view (GET)
            To pass the test, the view should return the tasks assigned to the current user
        """
        self.test_task_create()
        url = reverse("vpmotree:list_assigned_tasks", kwargs={"nodeID": str(self.project._id)})

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_task_status_update(self):
        """ Tests updating of the task status by the assignee """
        url = reverse("vpmotree:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)
        self.test_task_create()

        data = {
            "_id": str(self.task["_id"]),
            "status": "COMPLETE"
        }

        r = self.client.patch(url, json.dumps(data), content_type='application/json')

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "COMPLETE")

    def test_task_delete(self):
        """ Tests deletion of tasks """
        url = reverse("vpmotree:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)
        self.test_task_create()

        data = {
            "_id": str(self.task["_id"]),
        }

        r = self.client.delete(url, json.dumps(data), content_type='application/json')

        self.assertEqual(r.status_code, 200)