from django.shortcuts import render
from django.apps import apps

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.views import APIView

from vpmodoc.permissions import IsAdminOrContributor, HasTaskUpdatePermission
from vpmodoc.serializers import *
from vpmodoc.models import *
from vpmodoc import s3_utils
from vpmotree.models import TreeStructure
from vpmotask.models import Task


# Create your views here.

class NodeDocumentsListView(generics.ListAPIView):
	""" Returns all documents uploaded against the given node """
	serializer_class = NodeDocumentSerializer
	permission_classes = (permissions.IsAuthenticated, IsAdminOrContributor,)

	def get_queryset(self):
		return NodeDocument.objects.filter(node___id=self.kwargs["nodeID"])


class NodeDocumentsManagementView(APIView):
	permission_classes = (permissions.IsAuthenticated, IsAdminOrContributor,)

	def get_node(self):
		""" Returns the node based on the nodeID kwarg and the nodeType parameter """
		try:
			return TreeStructure.objects.get(_id=self.kwargs["nodeID"]).get_object()
		except TreeStructure.DoesNotExist:
			return None

	def get_document(self):
		try:
			return NodeDocument.objects.get(_id=self.request.query_params["docID"])
		except NodeDocument.DoesNotExist:
			return None

	def put(self, request, nodeID):
		""" Takes a docID in the request body along with a new name
			to rename the file associated with that node to
		"""
		doc = self.get_document()
		if doc is None:
			Response({"message": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

		new_name = request.data["newName"]
		doc.rename_document(new_name)

		return Response(NodeDocumentSerializer(doc).data)
		
	def post(self, request, nodeID):
		""" Returns the Put_Object presigned url for the given file name """
		node = self.get_node()
		if node is None:
			return Response({"message": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

		filename = NodeDocument.gen_filename(node, request.data["fileName"])
		presigned_url = s3_utils.generate_file_presigned_url(filename, client_method="put_object")

		return Response({
			"url": presigned_url,
			"file_name": filename
			})


class CreateNodeDocumentView(generics.CreateAPIView):
	""" Takes an input node and preuploaded filename as input
		and creates a Document model linked to the node from it
	"""
	serializer_class = NodeDocumentSerializer
	permission_classes = (permissions.IsAuthenticated, IsAdminOrContributor,)

	def get_node(self):
		""" Returns the node based on the nodeID kwarg and the nodeType parameter """
		try:
			return TreeStructure.objects.get(_id=self.kwargs["nodeID"]).get_object()
		except TreeStructure.DoesNotExist:
			return None

	def create(self, request, nodeID):
		data = request.data.copy()

		node = self.get_node()
		if not node:
			return Response({"message": "Node not found."}, status=status.HTTP_404_NOT_FOUND)

		try:
			create_data = {
				"document": data["fileName"],
				"node": node,
				"uploaded_by": request.user
			}
			doc = NodeDocument(**create_data)
			doc.save()
			# Returns all documents in node to save time with frontend development
			all_docs = NodeDocument.objects.filter(node___id=nodeID)
			return Response(self.serializer_class(all_docs, many=True).data, status=status.HTTP_201_CREATED)
		except:
			return Response({"message": "Error while creating document"}, status=status.HTTP_400_BAD_REQUEST)


class DestroyNodeDocumentView(APIView):
	""" Deletes the document and associated fiie object associated with it """
	permission_classes = (permissions.IsAuthenticated, IsAdminOrContributor,)

	def delete(self, request, docID=None, nodeID=None):
		try:
			doc = NodeDocument.objects.get(_id=docID)
		except NodeDocument.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

		# Delete the file from s3 if it exists (done by signal)
		doc.delete()

		return Response({"message": "Document deleted successfully."})


class TaskDocumentsManagementView(APIView):
	""" Implements a POST endpoint to return a presigned AWS url
		for an attachment upload against a task
	"""
	permission_classes = (permissions.IsAuthenticated, HasTaskUpdatePermission,)

	def get_task(self):
		""" Returns the task by matching ID against the url parameter """
		try:
			return Task.objects.get(_id=self.kwargs["taskID"])
		except Task.DoesNotExist:
			return None

	def post(self, request, taskID):
		""" Returns a presigned put_object permission for the given
			filename combined with the given taskID
		"""
		task = self.get_task()
		if task is None:
			return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

		filename = TaskDocument.gen_filename(task, request.data["fileName"])
		presigned_url = s3_utils.generate_file_presigned_url(filename, client_method="put_object")

		return Response({
			"url": presigned_url,
			"file_name": filename
			})


class CreateTaskDocumentView(generics.CreateAPIView):
	""" Creates the task document and assigns the s3 file
		from the fileName given as input
	"""
	permission_classes = (permissions.IsAuthenticated, HasTaskUpdatePermission,)
	serializer_class = TaskDocumentSerializer

	def get_task(self):
		""" Returns the task by matching ID against the url parameter """
		try:
			return Task.objects.get(_id=self.kwargs["taskID"])
		except Task.DoesNotExist:
			return None

	def create(self, request, taskID):
		data = request.data.copy()

		task = self.get_task()
		if task is None:
			return Response({"message": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

		try:
			create_data = {
				"document": TaskDocument.gen_filename(task, data["fileName"]),
				"task": task,
				"uploaded_by": request.user
			}
			doc = TaskDocument(**create_data)
			doc.save()

			return Response(self.serializer_class(doc).data, status=status.HTTP_201_CREATED)
		except:
			raise
			return Response({"message": "Error while creating document"}, status=status.HTTP_400_BAD_REQUEST)


class DestroyTaskDocumentView(APIView):
	""" Deletes the document and associated file from the db + s3 """
	permission_classes = (permissions.IsAuthenticated, HasTaskUpdatePermission,)

	def delete(self, request, taskID=None, docID=None):
		try:
			doc = TaskDocument.objects.get(_id=docID)
		except TaskDocument.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)

		# Delete the file from s3 if it exists (done by signal)
		doc.delete()

		return Response({"message": "Document deleted successfully."})