from django.urls import path
from vpmodoc import views

app_name = "vpmodoc"

urlpatterns = [
	path("api/node_documents/<str:nodeID>/", views.NodeDocumentsListView.as_view(), name="node_documents_list"),
	path("api/node_document_management/<str:nodeID>/", views.NodeDocumentsManagementView.as_view(), name="node_document_management"),
	path("api/create_node_document/<str:nodeID>/", views.CreateNodeDocumentView.as_view(), name="create_node_document"),
	path("api/delete_node_document/<str:nodeID>/<str:docID>/", views.DestroyNodeDocumentView.as_view(), name="destroy_node_document"),

	path("api/task_documents_management/<str:taskID>/", views.TaskDocumentsManagementView.as_view(), name="task_documents_management"),
	path("api/create_task_document/<str:taskID>/", views.CreateTaskDocumentView.as_view(), name="create_task_document"),
	path("api/delete_task_document/<str:taskID>/<str:docID>/", views.DestroyTaskDocumentView.as_view(), name="destroy_task_document")
]

