from djongo import models
from django.conf import settings
from vpmotree.models import TreeStructure
from vpmoauth.models import MyUser
from vpmodoc.s3_utils import generate_s3_client

# Create your models here.

class NodeDocument(models.Model):
    """ A Model defining a document (or file) uploaded against a node by a user """
    _id = models.ObjectIdField()
    
    # The file stored on S3 through django-storages
    # NOTE - To set this from an existing file, just save the model using document=<path_to_file_on_s3> (key)
    document = models.FileField()

    # The User who uploaded the file
    uploaded_by = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    # Node the document was uploaded against
    node = models.ForeignKey(TreeStructure, on_delete=models.CASCADE, related_name="node_documents")

    # Misc details
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "<Document:{}>".format(self.uploaded_by.username)

    def set_document(self, filename, document):
        """ Document MUST be a bytes object; ex: ContentFile(b'randText') """
        self.document.save(filename, document)

    def rename_document(self, new_name):
        """ Renames an s3 file by sending a copy object request
            from the old_name to the new_name
            new-name = a generic file name NOT prefixed by the nodeID
        """
        client = generate_s3_client()

        if self.document:
            # Copying over the old file to the new file
            source = {"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": self.document.name}
            new_name = self.gen_filename(self.node, new_name)
            response = client.copy_object(CopySource=source, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=new_name)
            # Setting the name in the database
            self.document.name = new_name
            self.save()

            return self.document.name
            
        return None

    def delete_document(self):
        if self.document:
            self.document.delete()
        return True

    @staticmethod
    def gen_filename(node, filename):
        return "{node_id}/{filename}".format(node_id=str(node._id), filename=filename)
