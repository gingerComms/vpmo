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
from django.apps import apps

from djongo import models
from django import forms

from vpmoprj.settings import AUTH_USER_MODEL

from django.core.mail import send_mail
import guardian.mixins

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)


class TreeStructure(models.Model):
    """ An implementation of Model Tree Structures with Materialized Paths in Django """
    _id = models.ObjectIdField()
    path = models.CharField(max_length=4048, null=True)
    # The index field is for tracking the location of an object within the heirarchy
    index = models.IntegerField(default=0, null=False)

    node_type = models.CharField(max_length=48, default="Team")

    # other than the Teams the rest of the nodes get created under (as a child)
    # OR at the same level of another node (sibling)
    # this means that Team starts a null path by itself,
    # the rest of the nodes get the path of the parent's node + the parent's objectId
    # OR the same path as the sibling node
    # e.g. the project immediately after team takes the team ID as its path
    # topic takes the team + project(s) above as its path
    # other than teams there is always a node which triggers the creation of child or sibling node
    # the triggering node provides its own path plus its id as the path for the new node

    def __str__(self):
        return '%s - %s' % (self._id, self.node_type)

class Team(TreeStructure):
    """ A Team is a ROOT level element in a TreeStructure; path is always None.
        * There is no save method because path is None by default
    """
    name = models.CharField(max_length=150, unique=False)
    # user_linked specifies whether the team is the default against user
    user_linked = models.BooleanField(default=False)
    user_team = models.CharField(max_length=251, unique=True)
    # Created at the registration time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.node_type = "Team"
        super(Team, self).save(*args, **kwargs)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s - %s' % (self.name, self.user_team)


class Project(TreeStructure):
    """ A Project is a BRANCH level element in a TreeStructure; 
        can have both Leaf and Branch children,
        can have both Root and Branch parents
    """
    name = models.CharField(max_length=150, null=False)
    description = models.TextField(blank=True, null=True)
    # content contains the WYSIWYG content coming in from the frontend
    content = models.TextField(blank=True, null=True)
    # team_project = models.CharField(max_length=452, null=False, unique=True, default=slugify(name) + '@')
    start = models.DateField(null=True)
    project_owner = models.ForeignKey('vpmoauth.MyUser',
                                      on_delete=models.PROTECT,
                                      null=True,
                                      related_name='%(class)s_project_owner')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.node_type = "Project"
        super(Project, self).save(*args, **kwargs)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

class Topic(TreeStructure):
    """ A Topic is a LEAF level element in a TreeStructure;
        can not have ANY children, and is always parented by a BRANCH Level element (Project)
    """
    name = models.CharField(max_length=150, null=False, unique=False)

    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)

    def save(self, *args, **kwargs):
        self.node_type = "Deliverable"
        super(Deliverable, self).save(*args, **kwargs)