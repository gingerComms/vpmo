# mongodb+srv://alifradn:mdEla45Jig!@cluster0-srrwy.mongodb.net/test
#
# connect(
#     'mongodb://alifradn:mdEla45Jig!@cluster0-shard-00-00-6qb6a.mongodb.net:27017,cluster0-shard-00-01-6qb6a.mongodb.net:27017,cluster0-shard-00-02-6qb6a.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin',
#     alias='my-atlas-app'
# )
from __future__ import unicode_literals
# from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from guardian import shortcuts
from django.apps import AppConfig

from djongo import models
from django import forms

from vpmoprj.settings import AUTH_USER_MODEL

from django.core.mail import send_mail
import guardian.mixins

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)


class NodeType(models.Model):
    # this model identifies the whether the TreeStructure node is a Team, Project, etc.
    _id = models.ObjectIdField()
    name = models.CharField(max_length=50, null=False, unique=True)

    def __str__(self):
        return '%s' % (self.name)


class TreeStructure(models.Model):
    """ An implementation of Model Tree Structures with Materialized Paths in Django """
    _id = models.ObjectIdField()
    path = models.CharField(null=False, max_length=4048)
    # The index field is for tracking the location of an object within the heirarchy
    index = models.IntegerField(default=0, null=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nodetype = models.ForeignKey(NodeType, on_delete=models.PROTECT, null=False)

    def get_element_path(self, elem=None):
        if elem is None:
            elem = self
        return str(elem._id)+"-{}".format(type(elem).__name__)

    def save(self, *args, **kwargs):
        # NOTE - Limit of recursion from MongoDB is 20! Do not create inheritances that exceed 20 levels!
        # If instance is a Team, just make sure the path is top level
        if isinstance(self, Team):
            self.path = ","+self.get_element_path()+","
        # If instance is a Project, set the path to parent's path + project_path
        elif isinstance(self, Project):
            if self.team is not None:
                self.path = self.team.path + "{},".format(self.get_element_path())
            elif self.parent_project is not None:
                self.path = self.parent_project.path + "{},".format(self.get_element_path())
        # Otherwise, just set path to parent project's (or parent topic's) path + current elem
        else:
            if getattr(self, "project", None):
                self.path = self.project.path + "{},".format(self.get_element_path())
            else:
                self.path = self.parent_topic.path + "{},".format(self.get_element_path())

        super(TreeStructure, self).save(*args, **kwargs)

    class Meta:
        abstract = True

    def __str__(self):
        return '%s' % (self.name)


class Team(TreeStructure):
    # user_linked specifies whether the team is the default against user
    # created at the registration time
    user_linked = models.BooleanField(default=False)
    user_team = models.CharField(max_length=151, unique=True)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s' % (self.userTeam)


class Project(TreeStructure):
    description = models.TextField(blank=True, null=True)
    start = models.DateField(null=True)
    project_owner = models.ForeignKey('vpmoauth.MyUser',
                                      on_delete=models.PROTECT,
                                      null=True,
                                      related_name='%(class)s_project_owner')

    # Many to One to both Teams and other Projects; one will always be null
    team = models.ForeignKey(Team, null=True, on_delete=models.PROTECT)
    parent_project = models.ForeignKey("self", null=True, on_delete=models.CASCADE)


    class Meta:
        ordering = ('name',)
        # objects = models.DjongoManager()


class Topic(TreeStructure):
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)
    parent_topic = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)