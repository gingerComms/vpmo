from django.test import TestCase, Client
from vpmotree.models import Team, Project, Deliverable
from vpmoauth.models import MyUser
from vpmotask.models import ScrumboardTaskList
import test_addons
from vpmotree import views
from django.shortcuts import reverse
from rest_framework.test import APIRequestFactory, force_authenticate
import os, json
import binascii
from copy import copy
from vpmotree import serializers
from create_base_permissions import create_base_permissions


# Create your tests here.
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

        self.project_admin.assign_role("project_admin", self.project, test=True)
        self.project_contributor.assign_role("project_contributor", self.project, test=True)

        self.task_list = ScrumboardTaskList(project=self.project, title="TaskListTest", index=0)
        self.task_list.save()

        self.client.force_login(self.project_admin)

    def tearDown(self):
        self.project.delete()
        self.project_admin.delete()
        self.project_contributor.delete()

    def test_task_assignee_update(self):
        self.test_task_create()

        url = reverse("vpmotask:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)

        data = {
            "assignee": str(self.project_admin.username),
            "_id": str(self.task["_id"])
        }

        r = self.client.put(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(str(r.json()["assignee"]["_id"]), str(self.project_admin._id))
        self.assertEqual(r.status_code, 200)

    def test_task_create(self):
        """ Tests the task creation POST endpoint """
        url = reverse("vpmotask:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)

        data = {
            "title": "Test Task",
            "status": "NEW",
            "due_date": "2018-10-07T18:30:00.000Z",
            "node": str(self.project._id),
            "task_list_id": str(self.task_list._id),
            "task_list_index": 0
        }

        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)
        self.task = r.json()

    def test_assignable_task_users(self):
        """ Tests the GET list view for assignable task users """
        self.test_task_create()
        url = reverse("vpmotask:assignable_task_users", kwargs={"nodeID": str(self.project._id)})+"?nodeType=Project"

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)


    def test_assigned_tasks_list(self):
        """ Tests the list method for tasks view (GET)
            To pass the test, the view should return the tasks assigned to the current user
        """
        self.test_task_create()
        url = reverse("vpmotask:list_assigned_tasks", kwargs={"nodeID": str(self.project._id)})

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_task_status_update(self):
        """ Tests updating of the task status by the assignee """
        url = reverse("vpmotask:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)
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
        url = reverse("vpmotask:delete_update_create_task")+"?nodeType=Project&nodeID="+str(self.project._id)
        self.test_task_create()

        data = {
            "_id": str(self.task["_id"]),
        }

        r = self.client.delete(url, json.dumps(data), content_type='application/json')

        self.assertEqual(r.status_code, 200)


class ScrumboardTaskListTestCase(TestCase):
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

        self.project_admin.assign_role("project_admin", self.project, test=True)

        self.client.force_login(self.project_admin)


    def test_task_list_create(self):
        url = reverse("vpmotask:scrumboard_task_list")

        data = {
            "project_id": str(self.project._id),
            "title": "TestTask",
            "index": 0
        }

        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["title"], "TestTask")
        self.task_list = r.json()


    def test_task_list_partial_update(self):
        self.test_task_list_create()
        url = reverse("vpmotask:scrumboard_task_list") + "?task_list=" + str(self.task_list["_id"]) \
                                                        + "?project_id=" + str(self.project._id)

        data = {
            "index": 1
        }

        r = self.client.patch(url, data)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["index"], 1)
