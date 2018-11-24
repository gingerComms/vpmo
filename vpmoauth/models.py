from django.conf import settings

from djongo import models
from django import forms

from django.db.models import Q
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group

from vpmoauth.managers import MyUserManager
from vpmoauth.role_permissions_map import ROLES_MAP
from vpmotree.models import Team, TreeStructure
from twilio.rest import Client


class UserRolePermission(models.Model):
    """ Model used to map permissions for nodes and roles """
    # This will be read_obj, update_obj etc.
    name = models.CharField(max_length=25)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """ A role representing a role a user has for a particular node """
    role_name = models.CharField(max_length=120, null=False)
    user = models.ForeignKey("vpmoauth.MyUser", on_delete=models.CASCADE, related_name="user_role_user", null=False)
    node = models.ForeignKey("vpmotree.TreeStructure", on_delete=models.CASCADE, related_name="user_role_node", null=False)

    # The Raason I'm going with a manytomanyfield over just having a Role name in UserRoloPermission
    #   is to avoid an extra django query. This way, I can just get the permissions in a single query using 
    #   a union.
    permissions = models.ManyToManyField("vpmoauth.UserRolePermission")

    def __str__(self):
        return "{} - {} - {}".format(self.role_name, self.user.username, self.node.node_type)

    @staticmethod
    def get_user_ids_with_perms(node):
        """ Returns users that have direct perms to the node """
        user_ids = UserRole.objects.filter(node=node).values_list("user___id", flat=True)
        return user_ids

    @staticmethod
    def get_user_ids_with_heirarchy_perms(node, perm_name):
        """ Returns Users that have access to the perm either directly or through a parent """
        node_branch = list(filter(lambda x: x.strip(), node.path.split(",") if node.path else '')) + [str(node._id)]
        user_ids = UserRole.objects.filter(node___id__in=node_branch, permissions__name=perm_name).values_list("user___id", flat=True)
        return user_ids

    @staticmethod
    def get_assigned_nodes(user, parent_node, perm_type="update"):
        """ Returns all nodes the user has the `perm_type` permission for """
        parent_node_condition = Q(node___id=parent_node) | Q(node__path__contains=parent_node)
        permission_condition = Q(permissions__name=perm_type+"_team") \
                                | Q(permissions__name=perm_type+"_project") \
                                | Q(permissions__name=perm_type+"_topic")

        node_ids = UserRole.objects.filter(
                        parent_node_condition,
                        permission_condition,
                        user=user
                    ).values_list("node___id", flat=True)
        return node_ids


# user.userrole_set.filter(node__id__in=[all_node_ids (parents + self)], permissions__permission_name__in=["read_topic"])


class MyUser(AbstractBaseUser):
    _id = models.ObjectIdField()
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    # email2 = models.EmailField(
    #     verbose_name='confirm email address',
    #     max_length=255,
    #     unique=True,
    # )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    fullname = models.CharField(max_length=100, null=True)
    username = models.CharField(max_length=100, unique=True, null=False)
    groups = models.ManyToManyField(Group, related_name="groups")

    # The nodes favorited by the user - shows up in the side bar
    favorite_nodes = models.ManyToManyField(TreeStructure, blank=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


    def get_email2(self):
        """ Arbitrary method used in the UserDeserializer for email validation """
        return "Email field for validation of email"

    def get_user_channels(self):
        """ Returns a list of channel objects assigned to this user """
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # This internally does a filter of channels that contain this user's username in it's members list
        channels = client.chat \
          .services(settings.TWILIO_CHAT_SERVICE_SID) \
          .users(self.username) \
          .user_channels \
          .list()
        return channels

    def remove_from_channel(self, channel):
        """ Removes this user from the given channel """
        # The username is the identity for the user in a channel
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        try:
            client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                .channels(channel) \
                .members(self.username) \
                .delete()
        except:
            return

        return True

    def add_to_channel(self, channel):
        """ Adds the user to the given channel """
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        try:
            member = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                        .channels(channel) \
                        .members \
                        .create(identity=self.username)
        except:
            return

        return member

    def update_channel_access(self, node, new_perms):
        """ Updates the user channel access for the given node branch
            Note: The assigned node is passed as the parent for get_assigned_nodes 
            because only the children of the assigned node or the assigned node itself
            have any chance of needing channels added
        """
        # The nodes  channels the user is added to
        user_channels = [i.channel_sid for i in self.get_user_channels()]
        nodes_already_added = TreeStructure.objects.filter(channel_sid__in=user_channels) \
                                .values_list("_id", flat=True)
        # The nodes the user has at least update access to
        accessible_nodes = UserRole.get_assigned_nodes(self, str(node._id), "update")

        # Nodes to remove is defined as channels the user is currently added to but can not access
        nodes_to_remove = [i for i in nodes_already_added if i not in accessible_nodes]
        # Nodes to add is defined as nodes the user can access but is not added to
        nodes_to_add = [i for i in accessible_nodes if i not in nodes_already_added]

        # Actually adding to and removing from the channels
        for i in nodes_to_remove:
            self.remove_from_channel(i)

        for i in nodes_to_add:
            self.add_to_channel(i)

        return accessible_nodes


    def assign_role(self, role, node, test=False):
        assert role in ROLES_MAP.keys()

        # Check if the user already has a role for this user, and remove it if it exists
        existing_role = UserRole.objects.filter(user=self, node=node).first()
        if existing_role is not None:
            if existing_role.role_name != role:
                existing_role.delete()
            else:
                return existing_role

        # Getting the permissions belonging to each orle
        permissions = ROLES_MAP[role]

        # Getting the permissions from the database
        permissions = UserRolePermission.objects.filter(name__in=permissions)

        role = {
            "role_name": role,
            "user": self,
            "node": node,
        }
        role = UserRole(**role)
        role.save()

        role.permissions.add(*permissions)
        role.save()

        # Removing/adding the user to the channel for this node based on the new role
        # If this isn't a test
        if not test:
            self.update_channel_access(node, permissions.values_list("name", flat=True))

        return role

    def remove_role(self, node):
        """ Removes the provided role from the current user for the node """
        # Removing from node channel
        self.remove_from_channel(str(node._id))
        # All the roles the user has for the node and the children of this node
        to_remove = UserRole.objects.filter(Q(node__path__contains=node._id) | Q(node___id=node._id), user=self)
        deleted = to_remove.delete()

        return deleted

    def get_permissions(self, node, all_types=False):
        """ Returns the list of permissions the user has for the given node """
        # All relevant node_ids for the permissions
        node_branch = list(filter(lambda x: x.strip(), node.path.split(",") if node.path else '')) + [str(node._id)]
        # Getting a merged list of any and all permissions the user has for this branch
        # node__id__in=node_branch filters all roles the user has for nodes in this branch of the treestructure
        # permissions__name__icontains=node.node_type filters only the permissions relevant to this node type
        filters = {
            "user": self,
            "node___id__in": node_branch,
        }
        if not all_types:
            filters["permissions__name__icontains"] = node.node_type

        permissions = UserRole.objects.filter(**filters).values_list("permissions__name", flat=True).distinct()
        return permissions

    def get_role(self, node):
        """ Returns the role the user has for this node - only direct role """
        role = UserRole.objects.filter(user=self, node=node).first()
        return role

    def is_team_owner(self, team):
        """ Returns True or False based on whether the current user is the team's owner """
        if not team.user_linked:
            return False

        if team.user_team == "team@{}".format(self.username):
            return True
        return False

    def create_user_team(self):
        # create a TreeStructure with nodetype of Team Linked to the user
        team = Team(
                name=self.username + "'s team",
                user_team="team@" + self.username,
                user_linked=True,
            )
        team.save()
        team.create_channel()
        # give the user created_obj permission against this team
        self.assign_role("team_admin", team)