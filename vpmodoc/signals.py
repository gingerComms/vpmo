from django.db.models.signals import pre_delete
from django.dispatch import receiver
from vpmodoc.models import NodeDocument

@receiver(pre_delete, sender=NodeDocument, dispatch_uid="doc_delete_signal")
def delete_document(sender, instance, using, **kwargs):
	print("Doc signal")
	instance.delete_document()