from __future__ import unicode_literals
# from django.db import models
from django.conf import settings
from django.apps import apps

from djongo import models
from django import forms

from twilio.rest import Client

# Create your models here.

class ScrumboardTaskList(models.Model):
	""" Represents a list in the scrumboard for a single project """
	_id = models.ObjectIdField()
	
	project = models.ForeignKey("vpmotree.Project", on_delete=models.CASCADE)
	title = models.CharField(max_length=255, unique=False, blank=False)
	index = models.IntegerField(default=0, null=False)

	def __str__(self):
		return self.title


class Task(models.Model):
    """ Represents a Tasks assignable to users for project/topic nodes """
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETE", "Complete"),
    ]

    _id = models.ObjectIdField()
    # The node can be a Project or a Subclass of Topic
    node = models.ForeignKey("vpmotree.TreeStructure", on_delete=models.CASCADE)

    title = models.CharField(max_length=255, unique=False, blank=False)
    content = models.TextField(blank=True)
    created_by = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE, related_name="created_task_set")
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)

    # The user the task is assigned to currently (defaults to created_by)
    assignee = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE, related_name="assigned_task_set")

    status = models.CharField(max_length=11, choices=STATUS_CHOICES, blank=False, unique=False)
    due_date = models.DateField(auto_now=False, auto_now_add=False, null=False)
    closed_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)

    # Relations with a task list
    task_list_index = models.IntegerField(default=0, null=False)
    task_list = models.ForeignKey("ScrumboardTaskList", on_delete=models.CASCADE, null=False)

    def __str__(self):
        return "<{title}>: {due_date}".format(title=self.title, due_date=self.due_date.strftime("%d/%m/%Y"))


    def save(self, *args, **kwargs):
        """ Minor amendments to save for generic conditions """
        if self.status != "COMPLETE":
            self.closed_at = None

        super(Task, self).save(*args, **kwargs)