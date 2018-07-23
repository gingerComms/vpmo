# mongodb+srv://alifradn:mdEla45Jig!@cluster0-srrwy.mongodb.net/test
#
# connect(
#     'mongodb://alifradn:mdEla45Jig!@cluster0-shard-00-00-6qb6a.mongodb.net:27017,cluster0-shard-00-01-6qb6a.mongodb.net:27017,cluster0-shard-00-02-6qb6a.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin',
#     alias='my-atlas-app'
# )
from __future__ import unicode_literals
# from django.db import models
from django.conf import settings
if settings.DEBUG:
    from django.db import models
    from django import forms
else:
    from djongo import models
    from djongo.models import forms
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Group
from django.core.mail import send_mail
from .managers import MyUserManager
import guardian.mixins

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)

class MyUser(AbstractBaseUser, guardian.mixins.GuardianUserMixin):
    id = models.IntegerField
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
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
    

class Comment(models.Model):
    content = models.TextField(blank=True, null=True)

    # def sample_view(self):
    #     current_user = self.user
    #     return current_user

    # author = sample_view()

    # author = models.ForeignKey(
    #     AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    # )
    def __str__(self):
        return '%s' % (self.content)

    class Meta:
        abstract = True


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'content',
        )


class Team(models.Model):
    name = models.CharField(max_length=50)
    # owner = models.ReferenceField(User)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s' % (self.name)


class Project(models.Model):
    projectname = models.CharField(max_length=50, verbose_name="Project Name")
    description = models.TextField(blank=True, null=True)
    # comments = models.ArrayModelField(
    #     model_container=Comment,
    #     model_form_class=CommentForm,
    #     null=True
    # )
    start = models.DateField(null=True)
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE)

    # organisation = models.ReferenceField(Organisation)
    # owner = models.ReferenceField(User)

    def __str__(self):
        return '%s' % (self.projectname)

    class Meta:
        ordering = ('projectname',)
    if not settings.DEBUG:
        objects = models.DjongoManager()

