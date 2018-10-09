from django.db import models
from django.conf import settings

from djongo import models
from django import forms

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from vpmoauth.managers import MyUserManager

from guardian.mixins import GuardianUserMixin
from guardian import shortcuts
from guardian.models import UserObjectPermission

from vpmotree.models import Team


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
        assert role in node.ROLE_MAP.keys()
        # Getting the permissions belonging to each orle
        to_assign = node.ROLE_MAP[role]

        # TODO - Remove any roles the user might have for one of the node's children (if any)
        #   Do the above after copnfirming with Ali

        # Assigning the role's permissions
        for perm in to_assign:
            print("Assigning perm {} for {} to {}".format(perm, self.username, node.__str__()))
            shortcuts.assign_perm(perm, self, node)
        self.save()
        return role

    def remove_role(self, node, role=None):
        """ Removes the provided role from the current user for the node """
        if role is None:
            role = self.get_role(node)

        perms = node.ROLE_MAP[role]
        UserObjectPermission.objects.filter(user=self, object_pk=node._id).delete()
        """
        for perm in perms:
            # Deleting the permission object directly
            UserObjectPermission.objects.filter(user=self, object_pk=node._id, permission__name=perm).delete()
            #shortcuts.remove_perm(perm, self, node)
        """
        self.save()
        return self.get_role(node)

    def get_role(self, node):
        perms = set(shortcuts.get_user_perms(self, node))
        role = [i for i in node.ROLE_MAP.keys() if set(node.ROLE_MAP[i]) == perms]
        if role:
            return role[0]
        return None

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