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

from djongo import models
from django import forms

from vpmoauth.models import MyUser
from vpmoprj.settings import AUTH_USER_MODEL



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


class TreeStructure(models.Model):
    """ An implementation of Model Tree Structures with Materialized Paths in Django """
    _id = models.ObjectIdField()
    path = models.CharField(null=False, max_length=4048)
    # The index field is for tracking the location of an object within the heirarchy
    index = models.IntegerField(default=0, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def get_element_path(self, elem=None):
        if elem is None:
            elem = self
        return str(elem._id)+"-{}".format(type(elem).__name__)

    def save(self, *args, **kwargs):
        # NOTE - Limit of recursion from MongoDB is 20! Do not create inheritances that exceed 20 levels!
        # If instance is a Team, just make sure the path is top level
        if isinstance(self, Team):
            self.path = ","+self.get_element_path()+","
        # If instance is a Project, set the path to parent's path + project_path
        elif isinstance(self, Project):
            if self.team is not None:
                self.path = self.team.path + "{},".format(self.get_element_path())
            elif self.parent_project is not None:
                self.path = self.parent_project.path + "{},".format(self.get_element_path())
        # Otherwise, just set path to parent project's (or parent topic's) path + current elem
        else:
            if getattr(self, "project", None):
                self.path = self.project.path + "{},".format(self.get_element_path())
            else:
                self.path = self.parent_topic.path + "{},".format(self.get_element_path())

        super(TreeStructure, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Team(TreeStructure):
    name = models.CharField(max_length=50)

    # user_linked specifies whether the team is the default against user
    # created at the registration time
    user_linked = models.BooleanField(default=False)
    userTeam = models.CharField(max_length=151, unique=True)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s' % (self.userTeam)


class Project(TreeStructure):
    projectname = models.CharField(max_length=50, verbose_name="Project Name", default="Project Name - Default")
    description = models.TextField(blank=True, null=True)

    start = models.DateField(null=True)
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)

    # Many to One to both Teams and other Projects; one will always be null
    team = models.ForeignKey(Team, null=True, on_delete=models.CASCADE)
    parent_project = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.projectname)

    class Meta:
        ordering = ('projectname',)
        # objects = models.DjongoManager()


class Topic(TreeStructure):
    name = models.CharField(max_length=240, default="N/A", unique=False)
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)
    parent_topic = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} - {type}".format(name=self.name, type=type(self).__name__)

    class Meta:
        abstract = True


class Deliverable(Topic):
    due_date = models.DateTimeField(auto_now=False, auto_now_add=False)


# def create_user_team(sender, instance, created, **kwargs):
#     if created:
#         # create a team Linked to the user
#         team = Team.objects.create(
#                 name=instance.username + "'s team",
#                 userTeam="team@" + instance.username,
#                 user_linked=True
#             )
#         team.save()
#         # User authentication
#
#         # give the user created_obj permission against this team
#         shortcuts.assign_perm("created_obj", instance, team)
#         # consider not to give any other user created_obj permission against this team
#
#         # print('user-team was created')
#
#
# post_save.connect(create_user_team, sender=MyUser)
