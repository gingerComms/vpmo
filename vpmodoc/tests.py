from django.test import TestCase, Client
from django.core.files.base import ContentFile
from django.shortcuts import reverse

from create_base_permissions import create_base_permissions

from vpmotree.models import Project
from vpmoauth.models import MyUser
from vpmodoc.models import NodeDocument

import json

# Create your tests here.

class NodeDocumentsTestCase(TestCase):
    """ Test Case containing all tests related to node documents """
    client = Client()

    def setUp(self):
        create_base_permissions()
        project_admin_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.project_admin = MyUser.objects.create(**project_admin_creds)

        self.project = Project(name="Test Proj", project_owner=self.project_admin)
        self.project.save()
        self.project_admin.assign_role("project_admin", self.project, test=True)

        self.client.force_login(self.project_admin)
        self.doc = self.create_document()

    def create_document(self, name="test_document.txt"):
        """ Creates a document with a test file through django-storages """
        # Creating the document
        doc = {
            "node": self.project,
            "uploaded_by": self.project_admin
        }
        doc = NodeDocument(**doc)
        doc.save()
        # Uploading a file
        doc.document.save(name, ContentFile(b"Test File Upload!"))

        return doc

    def tearDown(self):
        """ Deletes the created document and the file associated with it """
        if self.doc.document is not None:
            self.doc.document.delete()
        self.doc.delete()


    def test_document_list_view(self):
        """ Tests the NodeDocument List View """
        url = reverse("vpmodoc:node_documents_list", kwargs={"nodeID": str(self.project._id)}) + "?nodeType=Project"

        r = self.client.get(url)

        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)


    def test_presigned_url_upload(self):
        """ Tests the NodeDocument Presigned URL Post """
        url = reverse("vpmodoc:node_document_management", kwargs={"nodeID": str(self.project._id)}) + "?nodeType=Project"

        data = {"fileName": "Test.pdf"}
        r = self.client.post(url, data)

        self.assertEqual(r.status_code, 200)

    def test_document_delete(self):
        """ Tests the delete endpoint for documents """
        new_doc = self.create_document(name="deleteTest.txt")
        url = reverse("vpmodoc:destroy_node_document", kwargs={"docID": str(new_doc._id), "nodeID": str(self.project._id)}) + "?nodeType=Project"

        r = self.client.delete(url)

        self.assertEqual(r.status_code, 200)

    def test_document_rename(self):
        """ Tests the rename PUT endpoint for documents """
        new_doc = self.create_document(name="renameTest.txt")

        url = reverse("vpmodoc:node_document_management", kwargs={"nodeID": str(self.project._id)}) + "?nodeType=Project"
        url += "&docID=" + str(self.doc._id)

        data = {
            "newName": "renameTestSuccess.txt"
        }

        r = self.client.put(url, json.dumps(data), content_type='application/json')

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["document_name"], data["newName"])


class TaskDocumentsTestCase(TestCase):
    client = Client()

    def setUp(self):
        create_base_permissions()
        project_admin_creds = {
            "username": "TestUser",
            "email": "TestUser@vpmotest.com",
            "fullname": "Test User"
        }
        self.project_admin = MyUser(**project_admin_creds)
        self.project_admin.save()

        self.project = Project(name="Test Proj", project_owner=self.project_admin)
        self.project.save()
        self.project_admin.assign_role("project_admin", self.project, test=True)

        self.task = Task(node=project, title="TestTask", assignee=self.project_admin, status="NEW")
        self.task.save()

        self.client.force_login(self.project_admin)
        self.doc = None

    def create_document(self, name="test_document.txt"):
        """ Creates a document with a test file through django-storages """
        # Creating the document
        doc = {
            "task": self.task,
            "uploaded_by": self.project_admin
        }
        doc = TaskDocument(**doc)
        doc.save()
        # Uploading a file
        doc.set_document(name, ContentFile(b"Test File Upload!"))

        return doc

    def test_document_delete(self):
        """ Tests the DELETE endpoint for deleting taskDocs + s3 file """
        new_doc = self.create_document()
        url = reverse("vpmodoc:delete_task_document", kwargs={"taskID": str(self.task._id), "docID": new_doc._id})

        r = self.client.delete(url)

        self.assertEqual(r.status_code, 200)

    def test_document_presigned_put(self):
        """ Tests the POST endpoint for retrieving presigned put_object s3 url """
        url = reverse("vpmodoc:task_documents_management", kwargs={"taskID": str(self.task._id)})

        data = {
            "fileName": "test_document.txt"
        }

        r = self.client.post(url, data=data)

        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json().get("url", None) is not None)
