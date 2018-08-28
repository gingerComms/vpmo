from django.db import models
from django.conf import settings

from djongo import models
from django import forms

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from vpmoauth.managers import MyUserManager
from guardian.mixins import GuardianUserMixin
from guardian import shortcuts

from vpmotree.models import TreeStructure, NodeType


class MyUser(AbstractBaseUser, GuardianUserMixin):
    id = models.IntegerField
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
    username = models.CharField(max_length=100, unique=True)
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


    def create_user_team(self):
        # create a TreeStructure with nodetype of Team Linked to the user
        team = TreeStructure.objects.create(
                name=self.username + "'s team",
                userTeam="team@" + self.username,
                user_linked=True,
                nodetype=NodeType.objects.get(name="team")
            )
        team.save()
        # User authentication

        # give the user created_obj permission against this team
        shortcuts.assign_perm("created_obj", self, team)