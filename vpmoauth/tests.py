from django.test import TestCase, Client
from django.shortcuts import reverse
from vpmotree.models import Team, Project, Deliverable
from vpmoauth.models import MyUser
from vpmoauth import views
import os
import json
from create_base_permissions import create_base_permissions

# Create your tests here.

class FavoriteNodesTestCase(TestCase):
    """ Contains tests for the PUT and DELETE endpoints for favorite nodes """
    client = Client()

    def setUp(self):
        create_base_permissions()

        user_creds = {
            "username": "TestUser2",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.user = MyUser.objects.create(**user_creds)
        self.client.force_login(self.user)

        self.project = Project(name="Test Proj", project_owner=self.user)
        self.project.save()

        self.user.assign_role("project_admin", self.project, test=True)


    def test_favorite_add(self):
        """ Tests the PUT endpoint for adding favorite nodes """
        url = reverse("vpmoauth:favorite-nodes")

        data = {
            "node": str(self.project._id)
        }

        r = self.client.put(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["favorite_nodes"]), 1)

    def test_favorite_delete(self):
        """ Tests the DELETE endpoint for removing favorite nodes """
        self.test_favorite_add()
        url = reverse("vpmoauth:favorite-nodes")

        data = {
            "node": str(self.project._id)
        }

        r = self.client.delete(url, json.dumps(data), content_type='application/json')
        
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["favorite_nodes"]), 0)
    
