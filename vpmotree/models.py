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
from guardian import shortcuts

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

    def get_relatives(self, node_type, relation="parent"):
        """ Returns the nodes containing the current object's path based on node_type 
            NOTE - Includes self if node_type == self.node_type
        """
        model = apps.get_model("vpmotree", node_type)

        relatives = []
        children = []
        parents = []
        # Children are defined as nodes that contain the current obj's _id in their path
        if relation == "children" or relation is None:
            children = list(model.objects.filter(path__contains=self._id))
        # Parents are defined as nodes that are contained in the current obj's _id
        if self.path is not None and (relation == "parent" or relation is None):
            parents = filter(lambda x: len(x.strip()), self.path.split(","))
            parents = list(model.objects.filter(_id__in=parents))
        relatives = children + parents

        if node_type == self.node_type:
            relatives.append(self)

        return relatives


    def user_has_permission(self, user, permission):
        """ Returns true if the input user has the permission (even through a relative) to the current node  """
        node_types = []
        parents = []
        # If node is a Project/Team get Project and Team type parents
        if self.node_type == "Project" or self.node_type == "Deliverable":
            node_types += ["Project", "Team"]
            for node_type in node_types:
                parents += self.get_relatives(node_type, relation="parent")
        # If node is a Team, get only the team
        elif self.node_type == "Team":
            parents += [self]

        user_roles = {model:user.get_role(model) for model in parents}

        for model, role in user_roles.items():
            if role is not None:
                if permission in model.ROLE_MAP[role][self.node_type]:
                    return True
        return False


    def save(self, *args, **kwargs):
        super(TreeStructure, self).save(*args, **kwargs)

    def __str__(self):
        return '%s - %s' % (self._id, self.node_type)


class Team(TreeStructure):
    """ A Team is a ROOT level element in a TreeStructure; path is always None.
        * There is no save method because path is None by default
    """
    ROLE_MAP = {
        "team_admin":   {
            "Team": ["delete_obj", "update_obj", "read_obj", "add_user", "edit_role", "remove_user"],
            "Project": ["create_obj", "read_obj", "delete_obj", "update_obj"],
            "Deliverable": ["read_obj"]
        },
        "team_lead": {
            "Team": ["read_obj", "update_obj"],
            "Project": ["read_obj"],
            "Deliverable": ["read_obj"]
        },
        "team_member": {
            "Team": ["read_obj"],
        }
    }

    ASSIGN_MAP = {
        "team_admin": {
            "Team": ["team_lead", "team_member"],
            "Project": ["project_admin", "project_contributor", "project_viewer"]
        }
    }


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


    def get_users_with_role(self, role):
        """ Returns users with permissions based on the input role """
        # Returns users that have any perms for the object
        user_perms = shortcuts.get_users_with_perms(self, with_superusers=False, attach_perms=True)
        # Filtering those users to only the ones that have permissions from role_map
        return filter(lambda x: user_perms[x] == self.ROLE_MAP[role][self.node_type], user_perms)

    class Meta:
        permissions = (
            ("create_obj", "Create Level Permissions",),
            ('delete_obj', 'Delete Level Permissions',),
            ('update_obj', "Update Level Permissions",),
            ('read_obj', 'Read Level Permissions',),
            ("add_user", "Add User to Root",),
            ("remove_user", "Remove User from Tree",),
            ("edit_role", "Edit other user's role",)
        )

    def __str__(self):
        return '%s - %s' % (self.name, self.user_team)


class Project(TreeStructure):
    """ A Project is a BRANCH level element in a TreeStructure; 
        can have both Leaf and Branch children,
        can have both Root and Branch parents
    """
    ROLE_MAP = {
        "project_admin": {
            "Team": ["read_obj"],
            "Project": ["read_obj", "update_obj", "edit_role"],
            "Deliverable": ["create_obj", "read_obj", "delete_obj", "update_obj", "edit_role"]
        },
        "project_contributor": {
            "Project": ["read_obj", "edit_role"],
            "Deliverable": ["create_obj", "read_obj", "update_obj"]
        },
        "project_viewer": {
            "Project": ["read_obj"]
        }
    }

    ASSIGN_MAP = {
        "project_admin": {
            "Project": ["project_contributor", "project_admin", "project_viewer"],
            "Deliverable": ["topic_viewer", "topic_contributor"]
        },
        "project_contributor": {
            "Project": ["project_contributor", "project_viewer"],
            "Deliverable": ["topic_viewer", "topic_contributor"]
        }
    }

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

    def get_users_with_role(self, role):
        # Returns users that have any perms for the object
        user_perms = shortcuts.get_users_with_perms(self, with_superusers=False, attach_perms=True)
        # Filtering those users to only the ones that have permissions from role_map
        return filter(lambda x: user_perms[x] == self.ROLE_MAP[role][self.node_type], user_perms)

    class Meta:
        permissions = (
            ("create_obj", "Create Level Permissions",),
            ('delete_obj', 'Delete Level Permissions',),
            ('update_obj', "Update Level Permissions",),
            ('read_obj', 'Read Level Permissions',),
            ("edit_role", "Edit other user's role",)
        )

class Topic(TreeStructure):
    """ A Topic is a LEAF level element in a TreeStructure;
        can not have ANY children, and is always parented by a BRANCH Level element (Project)
    """
    ROLE_MAP = {
        "topic_contributor": {
            "Deliverable": ["read_obj", "edit_role"]
        },
        "topic_viewer": {
            "Deliverable": ["read_obj"]
        }
    }

    ASSIGN_MAP = {
        "topic_contributor": {
            "Deliverable": ["topic_viewer", "topic_contributor"]
        }
    }


    name = models.CharField(max_length=150, null=False, unique=False)
    # content = models.CharField(max_length=150, null=False, unique=False)
    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    def has_read_permissions(self, user):
        current_role = user.get_role(self)
        parent_role = user.get_role(self.get_parent())
        root_role = user.get_role(self.get_root())

        allowed_roles = ["team_admin", "team_lead", "project_admin", "project_contributor",
            "project_viewer", "topic_viewer", "topic_contributor"]
        if any(i in allowed_roles for i in [current_role, parent_role, root_role]):
            return True
        return False

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)

    def save(self, *args, **kwargs):
        self.node_type = "Deliverable"
        super(Deliverable, self).save(*args, **kwargs)

    class Meta:
        permissions = (
            ("create_obj", "Create Level Permissions",),
            ('delete_obj', 'Delete Level Permissions',),
            ('update_obj', "Update Level Permissions",),
            ('read_obj', 'Read Level Permissions',),
            ("edit_role", "Edit User Role Permissions",)
        )


class Message(models.Model):
    """ Represents every individual message in a Team's chatroom
        The Path for this model is set by the socket consumer whenever a new message is recieved
        - The index is basically set by the order the messages are received in (sent_on)
    """
    _id = models.ObjectIdField()
    node = models.ForeignKey(TreeStructure, on_delete=models.CASCADE)
    author = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE)
    content = models.CharField(max_length=250, null=False, unique=False)

    sent_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.author.email, self.sent_on.strftime("%m-%d-%Y %H:%M"))