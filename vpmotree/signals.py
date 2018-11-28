from django.db.models.signals import pre_delete
from django.dispatch import receiver
from vpmotree.models import *

@receiver(pre_delete, sender=TreeStructure, dispatch_uid='treestructure_delete_signal')
def delete_node_channel(sender, instance, using, **kwargs):
	instance.delete_channel()
