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
from django.apps import AppConfig
from django.apps import apps
from django.core.mail import send_mail

from djongo import models
from django import forms

from django.conf import settings

from twilio.rest import Client

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)


class Task(models.Model):
    """ Represents a Tasks assignable to users for project/topic nodes """
    STATUS_CHOICES = [
        ("NEW", "New"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETE", "Complete"),
    ]

    _id = models.ObjectIdField()
    # The node can be a Project or a Subclass of Topic
    node = models.ForeignKey("TreeStructure", on_delete=models.CASCADE)

    title = models.CharField(max_length=255, unique=False, blank=False)
    created_by = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE, related_name="created_task_set")
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)

    # The user the task is assigned to currently (defaults to created_by)
    assignee = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE, related_name="assigned_task_set")

    status = models.CharField(max_length=11, choices=STATUS_CHOICES, blank=False, unique=False)
    due_date = models.DateField(auto_now=False, auto_now_add=False, null=False)
    closed_at = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)

    def __str__(self):
        return "<{title}>: {due_date}".format(title=self.title, due_date=self.due_date.strftime("%d/%m/%Y"))


    def save(self, *args, **kwargs):
        """ Minor amendments to save for generic conditions """
        if self.status != "COMPLETE":
            self.closed_at = None

        super(Task, self).save(*args, **kwargs)


class TreeStructure(models.Model):
    """ An implementation of Model Tree Structures with Materialized Paths in Django """
    _id = models.ObjectIdField()
    path = models.CharField(max_length=4048, null=True)
    # The index field is for tracking the location of an object within the heirarchy
    index = models.IntegerField(default=0, null=False)

    node_type = models.CharField(max_length=48, default="Team")

    # The twilio channel SID for this node
    channel_sid = models.CharField(max_length=34, blank=False)

    # other than the Teams the rest of the nodes get created under (as a child)
    # OR at the same level of another node (sibling)
    # this means that Team starts a null path by itself,
    # the rest of the nodes get the path of the parent's node + the parent's objectId
    # OR the same path as the sibling node
    # e.g. the project immediately after team takes the team ID as its path
    # topic takes the team + project(s) above as its path
    # other than teams there is always a node which triggers the creation of child or sibling node
    # the triggering node provides its own path plus its id as the path for the new node

    objects = models.DjongoManager()

    def get_root(self):
        """ Returns the root element of the current tree structure """
        if self.path is None:
            return self
        # Getting the first element in the object's path (root)
        root_id = self.path.split(",")[1]
        # Getting the treestructure object followed by the actual node
        root = TreeStructure.objects.get(_id=root_id)
        node = apps.get_model("vpmotree", root.node_type)
        return node.objects.get(_id=root._id)

    def get_parent(self):
        if self.path == None:
            return
        parent = TreeStructure.objects.get(_id=self.path.split(',')[-2])
        # Return the particular node object based on parent's node_type
        if parent.node_type == "Team":
            return Team.objects.get(_id=parent._id)
        elif parent.node_type == "Project":
            return Project.objects.get(_id=parent._id)
        return parent


    def get_model_class(self):
        # Return the Node Type if it isn't set to topic
        if self.node_type != "Topic":
            return apps.get_model("vpmotree", self.node_type)
        # Otherwise, try to find each topic attr
        else:
            topic_types = ["deliverable", "issue"]
            for topic_type in topic_types:
                try:
                    return getattr(self, topic_type)._meta.model
                except Exception as e:
                    continue
        return

    def get_object(self):
        """ Returns the particular model instance for this treeStructure node """
        model = self.get_model_class()
        return model.objects.get(_id=self._id)

    def save(self, *args, **kwargs):
        super(TreeStructure, self).save(*args, **kwargs)

    def create_channel(self):
        """ Creates the twilio chat channel for this node
            Must be called after the object has been created
        """
        obj = self.get_object()
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        channel = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                    .channels \
                    .create(unique_name=self._id, friendly_name=obj.name)
        self.channel_sid = channel.sid
        self.save()

    def delete_channel(self):
        """ Deletes the channel related to this node """
        if self.channel_sid:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            channel = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                        .channels(str(self._id)) \
                        .delete()
            self.channel_sid = ""
            self.save()

    def get_users_in_channel(self):
        """ Returns all users part of this node's channel """
        if not self.channel_sid:
            raise ValueError("Node doesn't have a channel")

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # List of member objects for this channel
        members = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                     .channels(self._id) \
                     .members \
                     .list()

        return members

    def update_channel_access(self):
        """ Updates the channel access for all users that should have update access
            to this node - Only checks for additions because all removals are handled by
            `assign_role` currently - removal only happens when role is changed while
            addition can happen when node is created
            NOTE - MAY NOT BE NECESSARY SINCE HANDLOOED IN ASSIGN_ROLE
        """
        users_to_add = apps.get_model("vpmoauth", "UserRole") \
                        .get_user_ids_with_heirarchy_perms(self, "update_"+self.node_type.lower())
        users_to_add = apps.get_model("vpmoauth", "MyUser") \
                        .objects.filter(_id__in=users_to_add)

        # Adding the users to the channel
        for i in users_to_add:
            i.add_to_channel(str(self._id))

        return users_to_add


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


class Topic(TreeStructure):
    """ A Topic is a LEAF level element in a TreeStructure;
        can not have ANY children, and is always parented by a BRANCH Level element (Project)
    """

    topic_classes = [
        "Deliverable",
        "Issue",
    ]

    name = models.CharField(max_length=150, null=False, unique=False)
    content = models.TextField(blank=True, null=True)
    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)

    def save(self, *args, **kwargs):
        self.node_type = "Topic"
        super(Deliverable, self).save(*args, **kwargs)


class Issue(Topic):
    SEVERITY_CHOICES = [
        ('1', 'Low',),
        ('2', 'Medium',),
        ('3', "High",)
    ]
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)
    assignee = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE)
    severity = models.CharField(max_length=1, choices=SEVERITY_CHOICES, blank=False, default='1')

    def save(self, *args, **kwargs):
        self.node_type = "Topic"
        super(Issue, self).save(*args, **kwargs)