from django.db.models.signals import pre_delete
from django.dispatch import receiver
from vpmodoc.models import NodeDocument, TaskDocument

@receiver(pre_delete, sender=NodeDocument, dispatch_uid="node_doc_delete_signal")
@receiver(pre_delete, sender=TaskDocument, dispatch_uid="task_doc_delete_signal")
def delete_document(sender, instance, using, **kwargs):
	print("Doc Delete Signal")
	instance.delete_document()