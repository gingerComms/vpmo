from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from vpmotree.models import *
from vpmotask.models import ScrumboardTaskList
import logging

@receiver(pre_delete, sender=TreeStructure, dispatch_uid='treestructure_delete_signal')
def delete_node_channel(sender, instance, using, **kwargs):
	instance.delete_channel()


@receiver(post_save, sender=Project, dispatch_uid="project_post_save_signal")
def create_project_list(sender, instance, *args, **kwargs):
	""" Creates a task list if a project has no lists - to prevent errors during task creation """
	existing_task_lists = ScrumboardTaskList.objects.filter(project=instance).first()
	if existing_task_lists is None:
		created_task_list = ScrumboardTaskList(project=instance, title="Default List")
		created_task_list.save()
		