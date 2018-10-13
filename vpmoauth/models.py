from django.db import models
from django.conf import settings

from djongo import models
from django import forms

from django.db.models import Q
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group

from vpmoauth.managers import MyUserManager
from vpmoauth.role_permissions_map import ROLES_MAP
from vpmotree.models import Team

from guardian.mixins import GuardianUserMixin
from guardian import shortcuts
from guardian.models import UserObjectPermission


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
    def get_users_with_perms(self, node):
        user_ids = UserRole.objects.filter(node=node).values_list("user___id", flat=True)
        return MyUser.objects.filter(_id__in=user_ids)


# user.userrole_set.filter(node__id__in=[all_node_ids (parents + self)], permissions__permission_name__in=["read_topic"])


class MyUser(AbstractBaseUser, GuardianUserMixin):
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

    def assign_role(self, role, node):
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

        return role

    def remove_role(self, node):
        """ Removes the provided role from the current user for the node """
        # All the roles the user has for the node and the children of this node
        to_remove = UserRole.objects.filter(Q(node__path__contains=node._id) | Q(node___id=node._id), user=self)
        deleted = to_remove.delete()

        return deleted

    def get_permissions(self, node):
        """ Returns the list of permissions the user has for the given node """
        # All relevant node_ids for the permissions
        node_branch = filter(lambda x: x.strip(), node.path.split(",")) if node.path else [] + [node._id]
        # Getting a merged list of any and all permissions the user has for this branch
        # node__id__in=node_branch filters all roles the user has for nodes in this branch of the treestructure
        # permissions__name__icontains=node.node_type filters only the permissions relevant to this node type
        permissions = UserRole.objects.filter(user=self, node___id__in=node_branch, 
            permissions__name__icontains=node.node_type).values_list("permissions__name", flat=True).distinct()
        return permissions

    def get_role(self, node):
        """ Returns the role the user has for this node - only direct role """
        role = UserRole.objects.filter(user=self, node=node).first()
        return role

    def create_user_team(self):
        # create a TreeStructure with nodetype of Team Linked to the user
        team = Team(
                name=self.username + "'s team",
                user_team="team@" + self.username,
                user_linked=True,
            )
        team.save()
        # give the user created_obj permission against this team
        self.assign_role("team_admin", team)