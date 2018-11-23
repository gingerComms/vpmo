from django.urls import path
from vpmodoc import views

app_name = "vpmodoc"

urlpatterns = [
	path("api/node_documents/<str:nodeID>/", views.NodeDocumentsListView.as_view(), name="node_documents_list"),
	path("api/document_management_view/<str:nodeID>/", views.DocumentManagementView.as_view(), name="document_management"),
	path("api/create_document/<str:nodeID>/", views.CreateDocumentView.as_view(), name="create_document"),
	path("api/delete_document/<str:nodeID>/<str:docID>/", views.DestroyDocumentView.as_view(), name="destroy_document")
]

