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
if not settings.DEBUG:
    from django.db import models
    from django import forms
else:
    from djongo import models
    from djongo.models import forms
from vpmoauth.models import MyUser

from django.core.mail import send_mail
import guardian.mixins

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)




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
    user_linked = models.BooleanField(default=False)
    userTeam = models.CharField(max_length=151, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s' % (self.userTeam)


class Project(models.Model):
    projectname = models.CharField(max_length=50, verbose_name="Project Name", default="Project Name - Default")
    description = models.TextField(blank=True, null=True)
    # comments = models.ArrayModelField(
    #     model_container=Comment,
    #     model_form_class=CommentForm,
    #     null=True
    # )
    start = models.DateField(null=True)
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)

    # organisation = models.ReferenceField(Organisation)
    # owner = models.ReferenceField(User)

    def __str__(self):
        return '%s' % (self.projectname)

    class Meta:
        ordering = ('projectname',)
    if not settings.DEBUG:
        objects = models.DjongoManager()


# @receiver(pre_save, sender=Team)
# def my_callback(sender, instance, username, *args, **kwargs):
#     instance._id = slugify(instance.name) + '@' + username


def create_user_team(sender, instance, created, **kwargs):
    if created:
        # create a team Linked to the user
        team = Team.objects.create(
                                    name=instance.username + "'s team",
                                    userTeam="team@" + instance.username,
                                    user_linked=True
                                )
        # User authentication

        # give the user created_obj permission against this team
        shortcuts.assign_perm("created_obj", instance, team)
        # consider not to give any other user created_obj permission against this team

        print('user-team was created')


post_save.connect(create_user_team, sender=MyUser)
