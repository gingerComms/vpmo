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
        return '%s' % (self.name)

class Team(TreeStructure):
    """ A Team is a ROOT level element in a TreeStructure; path is always None.
        * There is no save method because path is None by default
    """
    name = models.CharField(max_length=150, unique=True)
    # user_linked specifies whether the team is the default against user
    user_linked = models.BooleanField(default=False)
    user_team = models.CharField(max_length=150, unique=True)
    # Created at the registration time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )


    def get_tree(self):
        """ Returns a nested dictionary of the TreeStructure (starting from the ROOT, self) """
        # TODO:
        #   Find ALL objects as x.path__contains=self._id
        #   Loop over those objects in levels; find ones that have two elements as 2nd level (branches) then 3 levels and so on until
        #   Leaves are reached at last level
        #   Use the serializers in serializers.py to Help get all the other fields of the element (except children, which we create
        #   in the nested loop)
        pass


    def __str__(self):
        return '%s - %s' % (self.name, self.user_team)


class Project(TreeStructure):
    """ A Project is a BRANCH level element in a TreeStructure; 
        can have both Leaf and Branch children,
        can have both Root and Branch parents
    """
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, null=True)
    start = models.DateField(null=True)
    project_owner = models.ForeignKey('vpmoauth.MyUser',
                                      on_delete=models.PROTECT,
                                      null=True,
                                      related_name='%(class)s_project_owner')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, parent_obj, *args, **kwargs):
        """ A Parent object is required during the save to set the path """
        # Since ROOT parents are valid (roots have null path), path can be defaulted to "," (if Null)
        self.path = parent_obj.path or "," + parent_obj._id + ","

        super(Project, self).save(*args, **kwargs)


class Topic(TreeStructure):
    """ A Topic is a LEAF level element in a TreeStructure;
        can not have ANY children, and is always parented by a BRANCH Level element (Project)
    """
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    def save(self, parent_obj, *args, **kwargs):
        """ A BRANCH level Parent object is required during the save to set the path """
        self.path = parent_obj.path + parent_obj._id + ","

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)